"""Generate bounded UDS C tables and the versioned PC catalogue from Excel.

Only this generator owns the UDS configuration. Validate all inputs before rendering,
stage all outputs, and restore previous files if a replacement fails. Existing content
outside the generated markers and all legacy catalogue sections are preserved.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PyCodeGene import LoadConfig_FromExcel

ROOT = Path(__file__).resolve().parents[4]
START = "/* CAUTION : Automatic generated code section: Start */"
END = "/* CAUTION : Automatic generated code section: End */"
TARGETS = {"STM32H753ZI": (512, 65536), "STM32G474RE": (256, 16384)}
SESSIONS = {"DEFAULT": 1, "PROGRAMMING": 2, "EXTENDED": 4}
SECURITY = {"NONE": 0, "MAINTENANCE": 1, "PROGRAMMING": 2}
TYPES = {
    "UINT8": ("t_uint8", 1, 0, 255),
    "UINT16": ("t_uint16", 2, 0, 65535),
    "UINT32": ("t_uint32", 4, 0, 4294967295),
    "SINT8": ("t_sint8", 1, -128, 127),
    "SINT16": ("t_sint16", 2, -32768, 32767),
    "SINT32": ("t_sint32", 4, -2147483648, 2147483647),
    "FLOAT32": ("t_float32", 4, -3.4028234663852886e38, 3.4028234663852886e38),
    "BYTES": ("t_uint8", None, 0, 0),
}
HANDLERS = {
    0x10: "APPUDS_ServiceSession", 0x11: "APPUDS_ServiceReset",
    0x22: "APPUDS_ServiceRead", 0x2E: "APPUDS_ServiceWrite",
    0x27: "APPUDS_ServiceSecurity", 0x29: "APPUDS_ServiceSecurity",
    0x31: "APPUDS_ServiceRoutine", 0x34: "APPUDS_ServiceDownload",
    0x36: "APPUDS_ServiceTransfer", 0x37: "APPUDS_ServiceExit",
    0x3E: "APPUDS_ServiceTester",
}
ROUTINES = {"APPUDS_RoutineVerify", "APPUDS_RoutineActivate"}
TABLE_COLUMNS = {
    "Uds_GeneralCfg": "Enabled EcuLogicalId CanNode RxCanId TxCanId CanIdFormat P2Ms P2StarMs S3Ms "
                      "IsoTpRxBufferSize IsoTpTxBufferSize MaxWritePayload BootloaderSupport SchemaVersion CatalogueVersion",
    "Uds_ServiceCfg": "SID Enabled HandlerSymbol AllowedSessions MinSecurityLevel AllowFunctional ResponseTimeoutMs",
    "Uds_DidCfg": "DID Name SourceModule SourceKey Type ByteLength ByteOrder ReadEnabled WriteEnabled "
                  "ReadSessions WriteSessions ReadSecurity WriteSecurity Min Max Scale Offset Unit "
                  "Persistence Precondition Enabled",
    "Uds_RoutineCfg": "RoutineId Name HandlerSymbol AllowedSessions MinSecurityLevel Precondition Enabled",
    "Uds_FlashCfg": "ProductId HwRevision BootloaderVersion MaxImageSize DownloadLogicalRegion "
                    "MaxBlockLength SignatureRequired RollbackPolicy",
}


def integer(value, label, minimum=0, maximum=0xFFFFFFFF):
    """Parse Excel integers without accepting truncation, booleans or expressions."""
    if isinstance(value, bool):
        raise ValueError(f"{label}: expected integer, not boolean")
    try:
        result = int(str(value).strip(), 0) if str(value).strip().lower().startswith("0x") else int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: invalid integer {value!r}") from exc
    if isinstance(value, float) and result != value:
        raise ValueError(f"{label}: fractional integer")
    if not minimum <= result <= maximum:
        raise ValueError(f"{label}: outside {minimum}..{maximum}")
    return result


def boolean(value, label):
    if value is True or str(value).upper() in ("TRUE", "1"):
        return True
    if value is False or str(value).upper() in ("FALSE", "0"):
        return False
    raise ValueError(f"{label}: expected TRUE or FALSE")


def symbol(value, label):
    result = str(value)
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", result):
        raise ValueError(f"{label}: invalid stable name {value!r}")
    return result


def numeric(value, fallback, label):
    result = float(fallback if value in (None, "") else value)
    if not math.isfinite(result):
        raise ValueError(f"{label}: expected finite number")
    return result


def rights(value, mapping, label):
    parts = [part.strip().upper() for part in str(value).split(",")]
    if not parts or any(part not in mapping for part in parts) or len(parts) != len(set(parts)):
        raise ValueError(f"{label}: unsupported or duplicate rights {value!r}")
    return sum(mapping[part] for part in parts)


def read_tables(workbook):
    reader = LoadConfig_FromExcel()
    reader.load_excel_file(str(workbook))
    tables = {}
    for name, required in TABLE_COLUMNS.items():
        data = reader.get_array_from_excel(name)
        if not data:
            raise ValueError(f"Missing named Excel table {name}; run tools/uds/add_excel_tables.py first")
        headers = [str(cell).strip() for cell in data[0]]
        if len(headers) != len(set(headers)) or set(required.split()) - set(headers):
            raise ValueError(f"{name}: missing or duplicate columns")
        tables[name] = [dict(zip(headers, row)) for row in data[1:] if any(v is not None for v in row)]
    business = reader.get_array_from_excel("AppSpm_PrmInfo")
    if not business:
        raise ValueError("Missing AppSpm_PrmInfo")
    tables["parameters"] = {}
    for row in business[1:]:
        if row[1] is None:
            continue
        key = symbol(row[1], "APPSPM name")
        if key in tables["parameters"]:
            raise ValueError(f"Duplicate APPSPM key {key}")
        tables["parameters"][key] = row
    for module, table in (("APPSNS", "AppSns_SnsInterface"), ("APPACT", "AppAct_ActInterface")):
        data = reader.get_array_from_excel(table) or []
        tables[module] = {str(row[1]): row for row in data[1:] if len(row) > 1 and row[1] is not None}
    return tables


def selected(rows, target):
    return [row for row in rows if row.get("Target") in (None, "", target)]


def unique(rows, key, label):
    seen = set()
    for row in rows:
        if row[key] in seen:
            raise ValueError(f"Duplicate {label}: {row[key]}")
        seen.add(row[key])


def validate(workbook, hardware):
    """Return one canonical intermediate model; never modify any output."""
    target = Path(hardware).stem.removesuffix("_HwCfg")
    if target not in TARGETS:
        raise ValueError(f"Unsupported V1 target {target}")
    reader = LoadConfig_FromExcel()
    reader.load_excel_file(str(hardware))
    cpu = reader.get_array_from_excel("CPU_Config")
    family = "stm32h7xx" if target == "STM32H753ZI" else "stm32g4xx"
    if not cpu or str(cpu[1][0]).lower() != family:
        raise ValueError("Hardware workbook family disagrees with target filename")
    fdcan = reader.get_array_from_excel("Fdcan_Info")
    tables = read_tables(workbook)
    general_rows = selected(tables["Uds_GeneralCfg"], target)
    if len(general_rows) != 1:
        raise ValueError(f"Exactly one Uds_GeneralCfg row required for {target}")
    g = copy.deepcopy(general_rows[0])
    if not re.fullmatch(r"V[0-9]+Pr[0-9]+", str(g["CatalogueVersion"])):
        raise ValueError("CatalogueVersion must explicitly name a VxxPryy version; ECU ID is not a revision")
    g["Enabled"] = boolean(g["Enabled"], "Enabled")
    g["BootloaderSupport"] = boolean(g["BootloaderSupport"], "BootloaderSupport")
    if g["BootloaderSupport"]:
        raise ValueError("BootloaderSupport requires independently approved board partitions, signature policy and HIL tests")
    for name, lower, upper in (("EcuLogicalId", 1, 65535), ("CanIdFormat", 11, 29),
                               ("P2Ms", 1, 65535), ("P2StarMs", 1, 65535),
                               ("S3Ms", 1, 0x7FFFFFFF), ("SchemaVersion", 1, 1),
                               ("IsoTpRxBufferSize", 8, TARGETS[target][0]),
                               ("IsoTpTxBufferSize", 8, TARGETS[target][0]),
                               ("MaxWritePayload", 1, TARGETS[target][0] - 3)):
        g[name] = integer(g[name], name, lower, upper)
    if g["CanIdFormat"] not in (11, 29):
        raise ValueError("CanIdFormat must be 11 or 29")
    for name in ("RxCanId", "TxCanId"):
        g[name] = integer(g[name], name, 0, (1 << g["CanIdFormat"]) - 1)
    if g["RxCanId"] == g["TxCanId"]:
        raise ValueError("Physical RX and TX IDs must differ")
    if not re.fullmatch(r"FMKFDCAN_NODE_[1-3]", str(g["CanNode"])):
        raise ValueError("Unknown CanNode")
    node = int(g["CanNode"][-1])
    if not fdcan or len(fdcan) <= node or fdcan[node][0] != f"FDCAN{node}" or min(fdcan[node][2:4]) <= 0:
        raise ValueError(f"{target}: selected FDCAN node has no allocated RX/TX resources")
    if not g["P2Ms"] <= g["P2StarMs"] < g["S3Ms"]:
        raise ValueError("Require P2 <= P2* < S3")
    if g["MaxWritePayload"] + 3 > g["IsoTpRxBufferSize"]:
        raise ValueError("Write payload exceeds receive capacity")
    # Every configured ECU on this shared example bus needs distinct physical identifiers.
    ids = set()
    ecu_ids = set()
    for row in tables["Uds_GeneralCfg"]:
        pair = {integer(row[name], name) for name in ("RxCanId", "TxCanId")}
        ecu_id = integer(row["EcuLogicalId"], "EcuLogicalId")
        if ids & pair or ecu_id in ecu_ids:
            raise ValueError("Physical ISO-TP CAN IDs or ECU logical identifiers collide")
        ids.update(pair)
        ecu_ids.add(ecu_id)
    services = []
    for row in selected(tables["Uds_ServiceCfg"], target):
        sid = integer(row["SID"], "SID", 0, 255)
        if HANDLERS.get(sid) != row["HandlerSymbol"]:
            raise ValueError(f"SID 0x{sid:02X}: handler must come from the compiled allowlist")
        item = dict(row, SID=sid, Enabled=boolean(row["Enabled"], "service Enabled"))
        item["session_mask"] = rights(row["AllowedSessions"], SESSIONS, "service sessions")
        if row["MinSecurityLevel"] not in SECURITY:
            raise ValueError("Service security must select one compiled authorization level")
        item["security"] = SECURITY[row["MinSecurityLevel"]]
        item["functional"] = boolean(row["AllowFunctional"], "AllowFunctional")
        item["timeout"] = integer(row["ResponseTimeoutMs"], "ResponseTimeoutMs", g["P2Ms"], 0x7FFFFFFF)
        if item["functional"] and sid in (0x2E, 0x11, 0x31, 0x34, 0x36, 0x37):
            raise ValueError("Mutating services cannot allow functional requests in this profile")
        services.append(item)
    unique(services, "SID", "SID")
    services.sort(key=lambda item: item["SID"])
    enabled_sids = {item["SID"] for item in services if item["Enabled"]}
    if g["Enabled"] and not {0x10, 0x3E}.issubset(enabled_sids):
        raise ValueError("Enabled UDS requires session control and TesterPresent")
    if enabled_sids & {0x34, 0x36, 0x37}:
        if not {0x10, 0x31, 0x34, 0x36, 0x37}.issubset(enabled_sids) or not g["BootloaderSupport"]:
            raise ValueError("Programming dependencies are incomplete")
        # Real Flash/signature provisioning has deliberately not been implemented in this application.
        raise ValueError("Production programming is disabled: board partition/signature/HIL approvals are required")
    dids = []
    for row in selected(tables["Uds_DidCfg"], target):
        item = dict(row)
        item["DID"] = integer(row["DID"], "DID", 0, 65535)
        item["Name"] = symbol(row["Name"], "DID Name")
        item["SourceKey"] = symbol(row["SourceKey"], "SourceKey")
        item["Enabled"] = boolean(row["Enabled"], "DID Enabled")
        for name in ("ReadEnabled", "WriteEnabled"):
            item[name] = boolean(row[name], name)
        if row["Type"] not in TYPES or row["ByteOrder"] not in ("BIG_ENDIAN", "LITTLE_ENDIAN"):
            raise ValueError("Unknown DID type or byte order")
        ctype, width, lower, upper = TYPES[row["Type"]]
        item["ByteLength"] = integer(row["ByteLength"], "ByteLength", 1, g["IsoTpTxBufferSize"] - 3)
        if width is not None and width != item["ByteLength"]:
            raise ValueError("DID wire type and ByteLength disagree")
        item["Min"] = numeric(row["Min"], lower, "Min")
        item["Max"] = numeric(row["Max"], upper, "Max")
        item["Scale"] = numeric(row["Scale"], 1, "Scale")
        item["Offset"] = numeric(row["Offset"], 0, "Offset")
        item["read_mask"] = rights(row["ReadSessions"], SESSIONS, "ReadSessions")
        item["write_mask"] = rights(row["WriteSessions"], SESSIONS, "WriteSessions")
        if row["ReadSecurity"] not in SECURITY or row["WriteSecurity"] not in SECURITY:
            raise ValueError("DID security must select one compiled authorization level")
        item["read_security"] = SECURITY[row["ReadSecurity"]]
        item["write_security"] = SECURITY[row["WriteSecurity"]]
        if not lower <= item["Min"] <= item["Max"] <= upper or item["Scale"] == 0:
            raise ValueError("DID bounds or scale are invalid")
        if item["WriteEnabled"] and (item["write_security"] == 0 or item["write_mask"] & 1):
            raise ValueError("Writes require authorization and a non-default session")
        if row["Precondition"] not in ("DENY", "NONE", "APPLICATION"):
            raise ValueError("Unbound precondition; add an explicit compiled business binding before using it")
        if item["WriteEnabled"] and item["ByteLength"] > g["MaxWritePayload"]:
            raise ValueError("Writable DID exceeds MaxWritePayload")
        module, key = row["SourceModule"], row["SourceKey"]
        if module == "APPSPM":
            if key not in tables["parameters"]:
                raise ValueError(f"Unknown APPSPM SourceKey {key}")
            source = tables["parameters"][key]
            source_type = "BYTES" if source[7] == "t_char" else next(
                (name for name, values in TYPES.items() if values[0] == source[7]), None)
            if source_type != row["Type"] or source[8] != item["ByteLength"]:
                raise ValueError(f"{key}: incompatible business type or size; structures need an explicit CUSTOM adapter")
            if (item["ReadEnabled"] and source[3] == "WO") or (item["WriteEnabled"] and source[3] == "RO"):
                raise ValueError(f"{key}: UDS cannot widen business access rights")
            if source_type != "BYTES":
                biz_min = numeric(source[4], lower, "business minimum")
                biz_max = numeric(source[5], upper, "business maximum")
                item["Min"] = numeric(row["Min"], biz_min, "Min")
                item["Max"] = numeric(row["Max"], biz_max, "Max")
                item["Scale"] = numeric(row["Scale"], source[9], "Scale")
                item["Offset"] = numeric(row["Offset"], source[10], "Offset")
                if not biz_min <= item["Min"] <= item["Max"] <= biz_max:
                    raise ValueError(f"{key}: UDS bounds widen business bounds")
                if item["Scale"] != float(source[9]) or item["Offset"] != float(source[10]):
                    raise ValueError(f"{key}: duplicate scaling contradicts APPSPM")
            if item["Persistence"] not in ("NONE", "APPSPM_NVM_DEFERRED"):
                raise ValueError("APPSPM has no durable-completion API; use APPSPM_NVM_DEFERRED explicitly")
            if source[12] is not None and item["Persistence"] != "APPSPM_NVM_DEFERRED":
                raise ValueError(f"{key}: existing NVM ownership must remain explicit")
            item["business_id"] = integer(source[0], "parameter id", 0, 65535)
        elif module in ("APPSNS", "APPACT"):
            if key not in tables[module] or row["Type"] != "FLOAT32":
                raise ValueError(f"{module}: unresolved public FLOAT32 business source {key}")
            if module == "APPSNS" and item["WriteEnabled"]:
                raise ValueError("Sensor sources are read-only")
        elif module == "APPSYS":
            if key != "ECU_POSITION" or row["Type"] != "UINT8" or item["WriteEnabled"]:
                raise ValueError("APPSYS supports only the public read-only ECU_POSITION binding")
        elif module != "CUSTOM":
            raise ValueError(f"Unknown SourceModule {module}")
        if module != "APPSPM" and item["Persistence"] != "NONE":
            raise ValueError("Only APPSPM owns persistence")
        dids.append(item)
    unique(dids, "DID", "DID")
    unique(dids, "Name", "DID Name")
    dids.sort(key=lambda item: item["DID"])
    if 1 + sum(2 + d["ByteLength"] for d in dids if d["Enabled"] and d["ReadEnabled"]) > g["IsoTpTxBufferSize"]:
        raise ValueError("Configured multi-DID response exceeds ISO-TP TX capacity")
    if any(d["Enabled"] and d["ReadEnabled"] for d in dids) and 0x22 not in enabled_sids:
        raise ValueError("Readable DIDs require enabled service 0x22")
    if any(d["Enabled"] and d["WriteEnabled"] for d in dids) and 0x2E not in enabled_sids:
        raise ValueError("Writable DIDs require enabled service 0x2E")
    routines = []
    for row in selected(tables["Uds_RoutineCfg"], target):
        item = dict(row, RoutineId=integer(row["RoutineId"], "RoutineId", 0, 65535),
                    Enabled=boolean(row["Enabled"], "routine Enabled"))
        symbol(row["Name"], "routine Name")
        if row["HandlerSymbol"] not in ROUTINES or row["Precondition"] not in ("DENY", "APPLICATION"):
            raise ValueError("Routine requires a compiled handler and explicit fail-closed precondition")
        item["session_mask"] = rights(row["AllowedSessions"], SESSIONS, "routine sessions")
        if row["MinSecurityLevel"] not in SECURITY:
            raise ValueError("Routine security must select one compiled authorization level")
        item["security"] = SECURITY[row["MinSecurityLevel"]]
        if item["security"] == 0 or item["session_mask"] != 2:
            raise ValueError("Programming routines require authorized programming session")
        routines.append(item)
    unique(routines, "RoutineId", "RoutineId")
    routines.sort(key=lambda item: item["RoutineId"])
    if any(r["Enabled"] for r in routines) and 0x31 not in enabled_sids:
        raise ValueError("Enabled routines require service 0x31")
    flash_rows = selected(tables["Uds_FlashCfg"], target)
    if len(flash_rows) != 1:
        raise ValueError("One target-specific Flash policy row is required")
    flash = dict(flash_rows[0])
    flash["backend"] = "DISABLED"
    flash["MaxImageSize"] = integer(flash["MaxImageSize"], "MaxImageSize", 0, TARGETS[target][1])
    flash["DownloadLogicalRegion"] = integer(flash["DownloadLogicalRegion"], "DownloadLogicalRegion")
    flash["MaxBlockLength"] = integer(flash["MaxBlockLength"], "MaxBlockLength", 3, g["MaxWritePayload"] + 2)
    if not boolean(flash["SignatureRequired"], "SignatureRequired"):
        raise ValueError("Flash must require a trusted signature")
    if flash["RollbackPolicy"] != "DISABLED_PENDING_BOARD_APPROVAL":
        raise ValueError("Real activation/rollback policy awaits approved board ports")
    return {"target": target, "general": g, "services": services, "dids": dids,
            "routines": routines, "firmware": flash, "parameters": tables["parameters"]}


def function_doc(name, params, local=False):
    """Generate API documentation once, on prototypes only."""
    result = f"/**\n * @brief Generated {name} business adapter.\n"
    result += " * @note Cyclic context; buffers are borrowed for this call and never retained.\n"
    for direction, param, description in params:
        result += f" * @param[{direction}] {param} : {description}.\n"
    return result + " * @retval RC_OK Completed.\n * @retval RC_ERROR_PARAM_INVALID Invalid binding or buffer size.\n */\n"


def adapters(dids):
    includes, declarations, implementations = set(), [], []
    for d in dids:
        if not d["Enabled"]:
            continue
        module, key, name = d["SourceModule"], d["SourceKey"], d["Name"]
        ctype, width, _, _ = TYPES[d["Type"]]
        for write in (False, True):
            if not d["WriteEnabled" if write else "ReadEnabled"]:
                continue
            operation = "Write" if write else "Read"
            callback = f"{'s_' if module != 'CUSTOM' else ''}UDSAPP_{operation}_{name}"
            signature = (f"t_eReturnCode {callback}(t_uint16 f_Key_u16, "
                         f"{'const ' if write else ''}t_uint8 * f_Data_pu8, t_uint16 f_Size_u16)")
            docs = function_doc(callback, [("in", "f_Key_u16", "Generated business identifier"),
                                           ("in" if write else "out", "f_Data_pu8", "Exact-size wire bytes"),
                                           ("in", "f_Size_u16", "Exact byte count")])
            declarations.append(docs + ("static " if module != "CUSTOM" else "") + signature + ";\n")
            if module == "CUSTOM":
                continue  # No weak fallback: a missing business implementation is a link error.
            if module == "APPSPM":
                includes.add('#include "APP_CTRL/APP_SPM/Src/APP_SPM_Access.h"')
            elif module in ("APPSNS", "APPACT", "APPSYS"):
                folder = {"APPSNS": "SNS", "APPACT": "ACT", "APPSYS": "SYS"}[module]
                includes.add(f'#include "APP_CTRL/APP_{folder}/Src/APP_{folder}.h"')
            body = (f"/*********************************\n * {callback}\n *********************************/\n"
                    f"static {signature}\n{{\n    t_eReturnCode Ret_e = RC_OK;\n    (void)f_Key_u16;\n\n"
                    "    //---- 1- Validate the generated exact wire size ----//\n"
                    "    if(f_Data_pu8 == NULL)\n    {\n        Ret_e = RC_ERROR_PTR_NULL;\n    }\n"
                    f"    else if(f_Size_u16 != {d['ByteLength']}U)\n    {{\n"
                    "        Ret_e = RC_ERROR_PARAM_INVALID;\n    }\n    else\n    {\n")
            if width is None:
                if write:
                    raise ValueError("Writable BYTES require an explicit CUSTOM atomic adapter")
                body += (f"        //---- 2- Read only through the public parameter API ----//\n"
                         f"        Ret_e = APPSPM_GetParam(APPSPM_PRM_{key}, f_Data_pu8, f_Size_u16);\n")
            else:
                suffix = "f32" if d["Type"] == "FLOAT32" else ("s" if d["Type"].startswith("SINT") else "u") + str(width * 8)
                variable = "value_" + suffix
                body += f"        {ctype} {variable} = 0;\n"
                if write:
                    body += ("        double decoded_f64 = 0.0;\n"
                             "        //---- 2- Decode the validated scalar before the atomic business update ----//\n"
                             f"        Ret_e = APPUDS_DecodeValue(&c_APPUDS_Dids_as[{d['index']}U], f_Data_pu8, &decoded_f64);\n"
                             "        if(Ret_e == RC_OK)\n        {\n"
                             f"            {variable} = ({ctype})decoded_f64;\n")
                    call = (f"APPSPM_SetParam(APPSPM_PRM_{key}, &{variable}, sizeof({variable}))" if module == "APPSPM"
                            else f"APPACT_SetActValue(APPACT_ACTITF_{key}, {variable})")
                    body += f"            Ret_e = {call};\n        }}\n"
                else:
                    body += "        //---- 2- Obtain a business snapshot through its public accessor ----//\n"
                    if module == "APPSPM":
                        body += f"        Ret_e = APPSPM_GetParam(APPSPM_PRM_{key}, &{variable}, sizeof({variable}));\n"
                    elif module == "APPACT":
                        body += f"        Ret_e = APPACT_GetActValue(APPACT_ACTITF_{key}, &{variable});\n"
                    elif module == "APPSNS":
                        body += ("        t_sAPPSNS_SnsValueInfo snapshot_s = {0};\n"
                                 f"        Ret_e = APPSNS_Get_SnsValue(APPSNS_SNSITF_{key}, &snapshot_s);\n"
                                 f"        {variable} = snapshot_s.SnsValue_f32;\n"
                                 "        if((Ret_e == RC_OK) && (snapshot_s.isValueOK_b == FALSE))\n        {\n"
                                 "            Ret_e = RC_WARNING_BUSY;\n        }\n")
                    else:
                        body += ("        t_eAPPSYS_EcuPos position_e = APPSYS_ECU_POS_NB;\n"
                                 "        Ret_e = APPSYS_GetEcuPosition(&position_e);\n"
                                 f"        {variable} = (t_uint8)position_e;\n")
                    body += "        if(Ret_e == RC_OK)\n        {\n            uint32_t raw_u32 = 0U;\n"
                    if d["Type"] == "FLOAT32":
                        body += f"            memcpy(&raw_u32, &{variable}, sizeof(raw_u32));\n"
                    else:
                        body += f"            raw_u32 = (uint32_t){variable};\n"
                    body += ("            //---- 3- Serialize explicit wire byte order ----//\n"
                             "            for(t_uint16 idx_u16 = 0U; idx_u16 < f_Size_u16; idx_u16++)\n            {\n")
                    shift = "(f_Size_u16 - 1U - idx_u16)" if d["ByteOrder"] == "BIG_ENDIAN" else "idx_u16"
                    body += (f"                f_Data_pu8[idx_u16] = (t_uint8)(raw_u32 >> (8U * {shift}));\n"
                             "            }\n        }\n")
            body += "    }\n\n    return Ret_e;\n}\n\n"
            implementations.append(body)
    return sorted(includes), declarations, implementations


def wrapped(content):
    return "/** @file Generated UDS configuration. Source: named Excel tables; use UDS_CodeGen.py. */\n" + START + "\n" + content + "\n" + END + "\n"


# Hardware-specific interrupt protection stays in the generated ConfigSpecific implementation.
QUEUE_CRITICAL_DECLARATIONS = """/**
 * @brief Save the interrupt mask and protect one bounded receive FIFO operation.
 * @note Main and CAN callback contexts. Never hold this section during FMKFDCAN or business operations.
 * @return Previous processor mask, restored by APPUDS_ExitQueueCritical_PRIVATE_.
 */
t_uint32 APPUDS_EnterQueueCritical_PRIVATE_(void);
/**
 * @brief Restore the exact interrupt mask after a bounded receive FIFO operation.
 * @param[in] f_Previous_u32 Mask returned by APPUDS_EnterQueueCritical_PRIVATE_.
 */
void APPUDS_ExitQueueCritical_PRIVATE_(t_uint32 f_Previous_u32);

"""

QUEUE_CRITICAL_IMPLEMENTATION = """/*********************************
 * APPUDS_EnterQueueCritical_PRIVATE_
 *********************************/
t_uint32 APPUDS_EnterQueueCritical_PRIVATE_(void)
{
    t_uint32 previous_u32 = 0U;

    //---- 1- Save and mask interrupts for a short queue operation ----//
#if !defined(PC_SIM)
    previous_u32 = __get_PRIMASK();
    __disable_irq();
    __DMB();
#endif

    return previous_u32;
}

/*********************************
 * APPUDS_ExitQueueCritical_PRIVATE_
 *********************************/
void APPUDS_ExitQueueCritical_PRIVATE_(t_uint32 f_Previous_u32)
{
    //---- 1- Restore exactly the prior interrupt state ----//
#if !defined(PC_SIM)
    __DMB();
    __set_PRIMASK(f_Previous_u32);
#else
    (void)f_Previous_u32;
#endif

    return;
}
"""


def render(model, catalogue):
    g = model["general"]
    dids = [dict(d, index=i) for i, d in enumerate(d for d in model["dids"] if d["Enabled"])]
    includes, declarations, implementations = adapters(dids)
    public = "#ifndef APPUDS_CONFIGPUBLIC_H_INCLUDED\n#define APPUDS_CONFIGPUBLIC_H_INCLUDED\n\n"
    for macro, value in (("ENABLED", int(g["Enabled"])), ("RX_BUFFER_SIZE", g["IsoTpRxBufferSize"]),
                         ("TX_BUFFER_SIZE", g["IsoTpTxBufferSize"]), ("MAX_WRITE_PAYLOAD", g["MaxWritePayload"])):
        public += f"/// @brief Excel-generated {macro.lower().replace('_', ' ')}.\n#define APPUDS_{macro} {value}U\n"
    public += "\n/// @brief Configured stable DID identifiers.\ntypedef enum\n{\n"
    for d in dids:
        public += f"    APPUDS_DID_{d['Name']} = 0x{d['DID']:04X}U,\n"
    public += f"    APPUDS_DID_NB = {len(dids)}U\n}} t_eAPPUDS_DidId;\n\n#endif\n"
    private = "#ifndef APPUDS_CONFIGPRIVATE_H_INCLUDED\n#define APPUDS_CONFIGPRIVATE_H_INCLUDED\n\n"
    for macro, value in (("CAN_NODE", g["CanNode"]), ("RX_CAN_ID", f"0x{g['RxCanId']:X}UL"),
                         ("TX_CAN_ID", f"0x{g['TxCanId']:X}UL"), ("CAN_ID_FORMAT", f"{g['CanIdFormat']}U"),
                         ("ECU_LOGICAL_ID", f"{g['EcuLogicalId']}U"), ("RX_QUEUE_SIZE", "16U"),
                         ("ISOTP_TIMEOUT_MS", "1000U")):
        private += f"/// @brief Generated {macro.lower().replace('_', ' ')}.\n#define APPUDS_{macro} {value}\n"
    private += "\n#endif\n"
    specific_h = ("#ifndef APPUDS_CONFIGSPECIFIC_H_INCLUDED\n#define APPUDS_CONFIGSPECIFIC_H_INCLUDED\n"
                  '#include "APP_CTRL/APP_UDS/Src/APP_UDS.h"\n'
                  "/// @brief Generated immutable server configuration.\nextern const t_sAPPUDS_Config c_APPUDS_Config_s;\n"
                  "#endif\n")
    custom_declarations = "\n".join(item for item in declarations if not item.splitlines()[-1].startswith("static "))
    specific_h = specific_h.replace("#endif\n", custom_declarations + "\n" +
                                      QUEUE_CRITICAL_DECLARATIONS + "#endif\n")
    specific = ('#include "APPUDS_ConfigSpecific.h"\n'
                '#include "APPUDS_ApplicationPort.h"\n'
                '#include "APP_CTRL/APP_UDS/Src/services/APPUDS_Services.h"\n'
                '#include "APP_CTRL/APP_UDS/Src/services/APPUDS_Programming.h"\n'
                '#include <stdint.h>\n#include <string.h>\n'
                '#if !defined(PC_SIM)\n#include <cmsis_gcc.h>\n#endif\n' + "\n".join(includes) + "\n\n")
    specific += "// Local functions - Prototypes\n" + "\n".join(declarations) + "\n"
    specific += f"/// @brief Sorted generated DID table.\nstatic const t_sAPPUDS_Did c_APPUDS_Dids_as[{max(1, len(dids))}] =\n{{\n"
    for d in dids:
        prefix = "" if d["SourceModule"] == "CUSTOM" else "s_"
        read = f"{prefix}UDSAPP_Read_{d['Name']}" if d["ReadEnabled"] else "NULL"
        write = f"{prefix}UDSAPP_Write_{d['Name']}" if d["WriteEnabled"] else "NULL"
        key = (f"APPSPM_PRM_{d['SourceKey']}" if d["SourceModule"] == "APPSPM" else f"0x{d['DID']:04X}U")
        specific += (f"    {{0x{d['DID']:04X}U, {key}, {d['ByteLength']}U, APPUDS_TYPE_{d['Type']},\n"
                     f"     {'TRUE' if d['ByteOrder'] == 'BIG_ENDIAN' else 'FALSE'}, {d['read_mask']}U, {d['write_mask']}U, "
                     f"{d['read_security']}U, {d['write_security']}U,\n"
                     f"     {d['Min']!r}, {d['Max']!r}, {read}, {write}, "
                     f"{'APPUDS_ApplicationCheck' if d['Precondition'] == 'APPLICATION' else 'APPUDS_DenyMaintenance'}}},\n")
    if not dids:
        specific += "    {0},\n"
    specific += "};\n\n"
    enabled = [s for s in model["services"] if s["Enabled"]]
    specific += f"/// @brief Generated service registry.\nstatic const t_sAPPUDS_Service c_APPUDS_Services_as[{max(1, len(enabled))}] =\n{{\n"
    for s in enabled:
        specific += (f"    {{0x{s['SID']:02X}U, {s['session_mask']}U, {s['security']}U, "
                     f"{'TRUE' if s['functional'] else 'FALSE'}, {s['timeout']}UL, {s['HandlerSymbol']}}},\n")
    if not enabled:
        specific += "    {0},\n"
    specific += "};\n\n"
    routines = [r for r in model["routines"] if r["Enabled"]]
    specific += f"/// @brief Generated routine registry.\nstatic const t_sAPPUDS_Routine c_APPUDS_Routines_as[{max(1, len(routines))}] =\n{{\n"
    for r in routines:
        specific += (f"    {{0x{r['RoutineId']:04X}U, {r['session_mask']}U, {r['security']}U, "
                     f"{'APPUDS_ApplicationCheck' if r['Precondition'] == 'APPLICATION' else 'APPUDS_DenyMaintenance'}, "
                     f"{r['HandlerSymbol']}}},\n")
    if not routines:
        specific += "    {0},\n"
    specific += ("};\n\n/// @brief Immutable, fail-closed application profile.\n"
                 "const t_sAPPUDS_Config c_APPUDS_Config_s =\n{\n"
                 f"    c_APPUDS_Dids_as, {len(dids)}U, c_APPUDS_Services_as, {len(enabled)}U,\n"
                 f"    c_APPUDS_Routines_as, {len(routines)}U, {g['P2Ms']}U, {g['P2StarMs']}U, {g['S3Ms']}UL,\n"
                 "    APPUDS_SendPayload_PRIVATE_, APPUDS_ApplicationCheck, APPUDS_ApplicationAuthenticate, NULL\n};\n\n")
    specific += "\n".join(implementations) + "\n" + QUEUE_CRITICAL_IMPLEMENTATION
    data = copy.deepcopy(catalogue)
    # Refresh PARAMETERS from the same Excel objects while keeping legacy per-item fields readable.
    parameters = {}
    for key, row in sorted(model["parameters"].items()):
        old = data.get("PARAMETERS", {}).get(key, {})
        item = dict(old, id=str(row[0]), machine=old.get("machine", 0))
        for field, index in (("min", 4), ("max", 5), ("default", 6)):
            item[field] = None if row[index] is None else str(row[index])
        item.update(type=row[7], byte_length=row[8], access=row[3], nvm_object=row[12])
        parameters[key] = item
    data["PARAMETERS"] = parameters
    uds = {"schema_version": g["SchemaVersion"], "target": model["target"], "enabled": g["Enabled"],
           "ecu_logical_id": g["EcuLogicalId"],
           "transport": {"rx_can_id": f"0x{g['RxCanId']:X}", "tx_can_id": f"0x{g['TxCanId']:X}",
                         "id_format": g["CanIdFormat"], "bitrate": 500000, "can_node": g["CanNode"],
                         "rx_buffer_size": g["IsoTpRxBufferSize"], "tx_buffer_size": g["IsoTpTxBufferSize"]},
           "timing": {"p2_ms": g["P2Ms"], "p2_star_ms": g["P2StarMs"], "s3_ms": g["S3Ms"]},
           "services": model["services"], "routines": model["routines"], "firmware": model["firmware"],
           "dids": {}}
    for d in model["dids"]:
        if not d["Enabled"]:
            continue
        uds["dids"][f"0x{d['DID']:04X}"] = {
            "name": d["Name"], "source_module": d["SourceModule"], "source_key": d["SourceKey"],
            "type": d["Type"], "byte_length": d["ByteLength"], "byte_order": d["ByteOrder"],
            "read": d["ReadEnabled"], "write": d["WriteEnabled"],
            "read_sessions": d["ReadSessions"].split(","), "write_sessions": d["WriteSessions"].split(","),
            "read_security": d["ReadSecurity"], "write_security": d["WriteSecurity"],
            "min": d["Min"], "max": d["Max"], "scale": d["Scale"], "offset": d["Offset"],
            "unit": d["Unit"], "persistence": d["Persistence"], "precondition": d["Precondition"],
        }
    data["UDS"] = uds
    return {"ConfigFiles/APPUDS_ConfigPublic.h": wrapped(public),
            "ConfigFiles/APPUDS_ConfigPrivate.h": wrapped(private),
            "ConfigSpecific/AppUdsConfigSpecific/APPUDS_ConfigSpecific.h": wrapped(specific_h),
            "ConfigSpecific/AppUdsConfigSpecific/APPUDS_ConfigSpecific.c": wrapped(specific),
            "catalogue": json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"}


def merge_generated(path, rendered):
    if not path.exists():
        return rendered.encode("utf-8")
    old = path.read_bytes().decode("utf-8")
    if old.count(START) != 1 or old.count(END) != 1 or old.index(START) >= old.index(END):
        raise ValueError(f"Refusing to overwrite unmanaged file {path}")
    middle = rendered.split(START, 1)[1].split(END, 1)[0]
    return (old.split(START, 1)[0] + START + middle + END + old.split(END, 1)[1]).encode("utf-8")


def atomic_outputs(outputs):
    """Stage the complete generation set; rollback replacements on a runtime failure.

    Each rename is atomic. Cross-file power-loss atomicity requires a filesystem-level
    snapshot and is not claimed. No outputs are touched on validation/render failure.
    """
    staged, originals, replaced = {}, {}, []
    try:
        for path, content in outputs.items():
            path = Path(path)
            original = path.read_bytes() if path.exists() else None
            if original == content:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            originals[path] = original
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
                stream.write(content)
                staged[path] = Path(stream.name)
        for path, temporary in staged.items():
            os.replace(temporary, path)
            replaced.append(path)
    except BaseException:
        for path in reversed(replaced):
            if originals[path] is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(originals[path])
        raise
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)


class UDS_CodeGen:
    """Entry point compatible with the existing application generation chain."""

    validate = staticmethod(validate)

    @staticmethod
    def code_generation(software_cfg_path, hardware_cfg_path, soft_udscfg_path, output_root=None):
        model = validate(software_cfg_path, hardware_cfg_path)
        catalogue_path = Path(soft_udscfg_path)
        existing = json.loads(catalogue_path.read_text(encoding="utf-8")) if catalogue_path.exists() else {}
        rendered = render(model, existing)
        destination = Path(output_root) if output_root else ROOT / "src/3_APP/APP_CFG"
        outputs = {destination / name: merge_generated(destination / name, content)
                   for name, content in rendered.items() if name != "catalogue"}
        outputs[catalogue_path] = rendered["catalogue"].encode("utf-8")
        atomic_outputs(outputs)
        return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("software", type=Path)
    parser.add_argument("hardware", type=Path)
    parser.add_argument("catalogue", type=Path)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    UDS_CodeGen.code_generation(args.software, args.hardware, args.catalogue, args.output_root)
