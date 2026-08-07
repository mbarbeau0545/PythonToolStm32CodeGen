"""
#  @file        FMKNVM_CodeGen.py
#  @brief       FMK_NVM configuration code generator.
#  @details     Generates logical partition/object configuration from Excel.
#               Physical storage layout is derived at runtime from backend geometry.
#
#  @author      mba
#  @date        jj/mm/yyyy
#  @version     1.0
"""
#------------------------------------------------------------------------------
#                                       IMPORT
#------------------------------------------------------------------------------

import os
from dataclasses import dataclass
from typing import Dict

current_dir = os.path.dirname(__file__)
root_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))

from PythonToolCfg.APP_PATH import *

from PyCodeGene import LoadConfig_FromExcel as LCFE, TARGET_T_ENUM_END_LINE, \
    TARGET_T_ENUM_START_LINE, TARGET_T_VARIABLE_START_LINE, \
    TARGET_T_VARIABLE_END_LINE

#------------------------------------------------------------------------------
#                                       CONSTANT
#------------------------------------------------------------------------------
FMKNVM_ENUM_ROOT_PART = "FMKNVM_PARTITION"
FMKNVM_ENUM_ROOT_OBJ = "FMKNVM_OBJECT"
FMKNVM_DEFAULT_SLOT_COUNT = 2

# Excel columns - FMKNVM_PartitionCfg
PART_COL_ID = 0
PART_COL_NAME = 1
PART_COL_PAYLOAD_CAPACITY = 2
PART_COL_FORMAT_VERSION = 3
PART_COL_QUIET_PERIOD_MS = 4
PART_COL_MAX_DEFERRED_COMMIT_MS = 5
PART_COL_MIN_COMMIT_INTERVAL_MS = 6
PART_COL_SLOT_COUNT = 7

# Excel columns - FMKNVM_ObjectCfg
OBJ_COL_ID = 0
OBJ_COL_NAME = 1
OBJ_COL_PARTITION = 2
OBJ_COL_SIZE = 3
OBJ_COL_VERSION = 4

#------------------------------------------------------------------------------
#                                       CLASS
#------------------------------------------------------------------------------
@dataclass
class PartitionCfg:
    payload_capacity: int
    format_version: int
    quiet_period: int
    max_deferred: int
    min_commit: int
    slot_count: int
    curr_size: int


@dataclass
class ObjectCfg:
    in_partition: str
    size: int
    version: int


class FMKNVM_CodeGen:
    """
    Generate:
      - FMKNVM_ConfigPublic.h:
          * partition enum
          * object enum
      - FMKNVM_ConfigPrivate.h:
          * partition descriptors
          * object descriptors
          * partition RAM caches

    Important:
      Physical partition offset/size/slot stride are not generated here.
      FMK_NVM derives them at runtime from:
        - payloadCapacity_u32
        - slotCount_u16
        - backend geometry/capabilities
    """

    code_gen = LCFE()

    @staticmethod
    def _read_optional_int(row, index: int, default: int) -> int:
        """Read an optional integer Excel cell and return default when empty."""
        if index >= len(row):
            return default

        value = row[index]
        if value is None:
            return default

        text = str(value).strip()
        if text == "" or text.lower() == "nan":
            return default

        return int(value)

    @classmethod
    def code_generation(cls, f_hw_cfg) -> None:
        partition_cfg_a = []
        object_cfg_a = []

        if isinstance(f_hw_cfg, str) and os.path.isfile(f_hw_cfg) and os.path.getsize(f_hw_cfg) > 0:
            try:
                cls.code_gen.load_excel_file(f_hw_cfg)
                partition_cfg_a = cls.code_gen.get_array_from_excel("FMKNVM_PartitionCfg")
                object_cfg_a = cls.code_gen.get_array_from_excel("FMKNVM_ObjectCfg")
            except Exception as exc:
                print(
                    f"[WARNING] : FMKNVM_Codegen -> invalid or unreadable config file "
                    f"'{f_hw_cfg}', generate minimal code ({exc})"
                )
        else:
            print(
                f"[WARNING] : FMKNVM_Codegen -> config file missing or empty "
                f"'{f_hw_cfg}', generate minimal code"
            )

        partition_cfg_a = partition_cfg_a[1:] if partition_cfg_a is not None else []
        object_cfg_a = object_cfg_a[1:] if object_cfg_a is not None else []

        #-----------------------------------------------------------------
        #-----------------------------make all enum-----------------------
        #-----------------------------------------------------------------
        if partition_cfg_a:
            enum_part = cls.code_gen.make_enum_from_variable(
                FMKNVM_ENUM_ROOT_PART,
                [str(part_cfg[PART_COL_NAME]).upper() for part_cfg in partition_cfg_a],
                't_eFMKNVM_PartitionId',
                0,
                'Identifies one transactional persistent partition.',
                []
            )
        else:
            enum_part = cls.code_gen.make_enum_from_variable(
                FMKNVM_ENUM_ROOT_PART,
                [],
                't_eFMKNVM_PartitionId',
                0,
                'Identifies one transactional persistent partition.',
                []
            )

        if object_cfg_a:
            enum_obj = cls.code_gen.make_enum_from_variable(
                FMKNVM_ENUM_ROOT_OBJ,
                [str(obj_cfg[OBJ_COL_NAME]).upper() for obj_cfg in object_cfg_a],
                't_eFMKNVM_ObjectId',
                0,
                'Identifies one logical value stored inside a partition.',
                []
            )
        else:
            enum_obj = cls.code_gen.make_enum_from_variable(
                FMKNVM_ENUM_ROOT_OBJ,
                [],
                't_eFMKNVM_ObjectId',
                0,
                'Identifies one logical value stored inside a partition.',
                []
            )

        list_part_cfg: Dict[str, PartitionCfg] = {}
        list_obj_cfg: Dict[str, ObjectCfg] = {}

        # The C core reserves this bitmap at the beginning of every partition payload.
        validity_bitmap_size = (len(object_cfg_a) + 7) // 8

        #-----------------------------------------------------------------
        #----------------------parse partition config---------------------
        #-----------------------------------------------------------------
        for part_row in partition_cfg_a:
            name = str(part_row[PART_COL_NAME]).strip().upper()

            payload_capacity = int(part_row[PART_COL_PAYLOAD_CAPACITY])
            format_version = int(part_row[PART_COL_FORMAT_VERSION])
            quiet_period = int(part_row[PART_COL_QUIET_PERIOD_MS])
            max_deferred = int(part_row[PART_COL_MAX_DEFERRED_COMMIT_MS])
            min_commit = int(part_row[PART_COL_MIN_COMMIT_INTERVAL_MS])
            slot_count = cls._read_optional_int(
                part_row,
                PART_COL_SLOT_COUNT,
                FMKNVM_DEFAULT_SLOT_COUNT
            )

            if name in list_part_cfg:
                raise ValueError(f"{name} is already a partition name given")

            if payload_capacity <= 0:
                raise ValueError(f"{name}: payload capacity must be greater than 0")

            if payload_capacity > 0xFFFF:
                raise ValueError(f"{name}: payload capacity must fit in uint16 persistent format")

            if payload_capacity < validity_bitmap_size:
                raise ValueError(
                    f"{name}: payload capacity must reserve at least "
                    f"{validity_bitmap_size} bytes for the validity bitmap"
                )

            if format_version <= 0 or format_version > 0xFFFF:
                raise ValueError(f"{name}: format version must be in [1, 65535]")

            if slot_count < 2 or slot_count > 0xFFFF:
                raise ValueError(f"{name}: slot count must be in [2, 65535]")

            if quiet_period < 0 or max_deferred < 0 or min_commit < 0:
                raise ValueError(f"{name}: commit timings cannot be negative")

            list_part_cfg[name] = PartitionCfg(
                payload_capacity=payload_capacity,
                format_version=format_version,
                quiet_period=quiet_period,
                max_deferred=max_deferred,
                min_commit=min_commit,
                slot_count=slot_count,
                curr_size=validity_bitmap_size
            )

        #-----------------------------------------------------------------
        #------------------------generate objects-------------------------
        #-----------------------------------------------------------------
        var_obj = "    /// @brief Logical object mapping generated for the current application.\n"
        var_obj += (
            f"    static const t_sFMKNVM_ObjectDescriptor "
            f"c_FMKNVM_ObjectDescriptors_as[{FMKNVM_ENUM_ROOT_OBJ}_NB] = {{\n"
        )

        size_part_overpass = []

        for obj_row in object_cfg_a:
            name = str(obj_row[OBJ_COL_NAME]).strip().upper()
            partition_name = str(obj_row[OBJ_COL_PARTITION]).strip().upper()

            obj_cfg = ObjectCfg(
                in_partition=partition_name,
                size=int(obj_row[OBJ_COL_SIZE]),
                version=int(obj_row[OBJ_COL_VERSION])
            )

            if name in list_obj_cfg:
                raise ValueError(f"{name} already an object name --> {list_obj_cfg}")

            if obj_cfg.size <= 0:
                raise ValueError(f"{name}: object size must be greater than 0")

            if obj_cfg.version <= 0 or obj_cfg.version > 0xFFFF:
                raise ValueError(f"{name}: object version must be in [1, 65535]")

            if obj_cfg.in_partition not in list_part_cfg:
                raise ValueError(
                    f"{obj_cfg.in_partition} not in partition list -> "
                    f"{list_part_cfg.keys()}"
                )

            list_obj_cfg[name] = obj_cfg
            partition_cfg = list_part_cfg[obj_cfg.in_partition]
            curr_part_offset = partition_cfg.curr_size
            required_size = curr_part_offset + obj_cfg.size

            if required_size > partition_cfg.payload_capacity:
                if obj_cfg.in_partition not in size_part_overpass:
                    size_part_overpass.append(obj_cfg.in_partition)

            var_obj += (
                f"        [{FMKNVM_ENUM_ROOT_OBJ}_{name}] = {{\n"
                f"            .partitionId_e = {FMKNVM_ENUM_ROOT_PART}_{obj_cfg.in_partition},\n"
                f"            .offset_u32 = (t_uint32){curr_part_offset}U,\n"
                f"            .size_u32 = (t_uint32){obj_cfg.size}U,\n"
                f"            .version_u16 = (t_uint16){obj_cfg.version}U,\n"
                f"        }},\n"
            )

            partition_cfg.curr_size = required_size

        var_obj += "    };\n\n"

        if size_part_overpass:
            details = "".join(
                f"\tfor {part_name}: {list_part_cfg[part_name].curr_size} bytes\n"
                for part_name in size_part_overpass
            )

            raise ValueError(
                "At least one partition payload is not large enough --> "
                "should be at least:\n" + details
            )

        #-----------------------------------------------------------------
        #--------------------generate partition config--------------------
        #-----------------------------------------------------------------
        var_part = "    /// @brief Logical partition definitions independent of the selected backend.\n"
        var_part += (
            f"    static const t_sFMKNVM_PartitionDescriptor "
            f"c_FMKNVM_PartitionDescriptors_as[{FMKNVM_ENUM_ROOT_PART}_NB] = {{\n"
        )
        max_payload_capacity = max(
            (part_cfg.payload_capacity for part_cfg in list_part_cfg.values()),
            default=0
        )

        generated_max_payload_capacity = max(max_payload_capacity, 1)
        var_cache = (
            "    /// @brief Maximum payload capacity generated from FMKNVM_PartitionCfg.\n"
            "    #define FMKNVM_MAX_PARTITION_PAYLOAD_CAPACITY "
            f"((t_uint32){generated_max_payload_capacity}U)\n\n"
        )

        for name, part_cfg in list_part_cfg.items():
            part_var_cache = f"g_FMKNVM_{name.capitalize()}Cache_au8"

            var_cache += f"    /// @brief RAM cache for all {name.capitalize()} objects\n"
            var_cache += (
                f"    static t_uint8 {part_var_cache}"
                f"[{part_cfg.payload_capacity}];\n\n"
            )

            var_part += (
                f"        [{FMKNVM_ENUM_ROOT_PART}_{name}] = {{\n"
                f"            .cacheData_pu8 = {part_var_cache},\n"
                f"            .payloadCapacity_u32 = (t_uint32){part_cfg.payload_capacity}U,\n"
                f"            .formatVersion_u16 = (t_uint16){part_cfg.format_version}U,\n"
                f"            .quietPeriodMs_u32 = (t_uint32){part_cfg.quiet_period}U,\n"
                f"            .maximumDeferredCommitMs_u32 = (t_uint32){part_cfg.max_deferred}U,\n"
                f"            .minimumCommitIntervalMs_u32 = (t_uint32){part_cfg.min_commit}U,\n"
                f"            .slotCount_u16 = (t_uint16){part_cfg.slot_count}U,\n"
                f"        }},\n"
            )

        var_part += "    };\n\n"

        #-----------------------------------------------------------------
        #------------------------make code gen----------------------------
        #-----------------------------------------------------------------
        print('[INFO] : FMKNVM_Codegen -> Config Public Code Generation')
        cls.code_gen.change_target_balise(
            TARGET_T_ENUM_START_LINE,
            TARGET_T_ENUM_END_LINE
        )
        cls.code_gen._write_into_file(enum_obj, FMKNVM_CFG_PUBLIC)
        cls.code_gen._write_into_file(enum_part, FMKNVM_CFG_PUBLIC)

        print('[INFO] : FMKNVM_Codegen -> Config Private Code Generation')
        cls.code_gen.change_target_balise(
            TARGET_T_VARIABLE_START_LINE,
            TARGET_T_VARIABLE_END_LINE
        )
        cls.code_gen._write_into_file(var_obj, FMKNVM_CFG_PRIVATE)
        cls.code_gen._write_into_file(var_part, FMKNVM_CFG_PRIVATE)
        cls.code_gen._write_into_file(var_cache, FMKNVM_CFG_PRIVATE)