"""
#  @file        AppSpm_CodeGen.py
#  @brief       APP_SPM configuration and typed API generator.
#  @details     Generates parameter identifiers, exact-size RAM caches,
#               descriptors and one strongly typed Get/Set API per parameter.\n
#
#  @author      mba
#  @date        jj/mm/yyyy
#  @version     1.1
"""
#------------------------------------------------------------------------------
#                                       IMPORT
#------------------------------------------------------------------------------

import os
import json

current_dir = os.path.dirname(__file__)
root_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))

from PythonToolCfg.APP_PATH import *
from PyCodeGene import LoadConfig_FromExcel as LCFE, \
    TARGET_T_ENUM_END_LINE, TARGET_T_ENUM_START_LINE, \
    TARGET_T_VARIABLE_START_LINE, TARGET_T_VARIABLE_END_LINE

#------------------------------------------------------------------------------
#                                       CONSTANT
#------------------------------------------------------------------------------
APPSPM_ENUM_ROOT_PARAM = "APPSPM_PRM"
APPSPM_ENUM_ROOT_PRM_TYPE = "APPSPM_PRM_TYPE"
APPSPM_ENUM_ROOT_ACESS = "APPSPM_PRM_ACCESS"

TARGET_T_PARAM_API_DECL_START_LINE = \
    "/* CAUTION : Automatic generated code section for Parameter API Declaration: Start */\n"
TARGET_T_PARAM_API_DECL_END_LINE = \
    "/* CAUTION : Automatic generated code section for Parameter API Declaration: End */\n"
TARGET_T_PARAM_API_IMPL_START_LINE = \
    "/* CAUTION : Automatic generated code section for Parameter API Implementation: Start */\n"
TARGET_T_PARAM_API_IMPL_END_LINE = \
    "/* CAUTION : Automatic generated code section for Parameter API Implementation: End */\n"

# Excel AppSpm_PrmInfo columns currently used by the generator.
APPSPM_COL_ID = 0
APPSPM_COL_NAME = 1
APPSPM_COL_VERSION = 2
APPSPM_COL_ACCESS = 3
APPSPM_COL_MIN = 4
APPSPM_COL_MAX = 5
APPSPM_COL_DEFAULT = 6
APPSPM_COL_C_TYPE = 7
APPSPM_COL_SIZE = 8
APPSPM_COL_FACTOR = 9
APPSPM_COL_OFFSET = 10
APPSPM_COL_SIGNAL = 11
APPSPM_COL_NVM_OBJECT = 12
# Optional column. Required only for non-standard/custom types such as STRUCT.
# Example: Type="STRUCT", CType="t_sMyMachineCfg".

APPSPM_SCALAR_C_TYPES = [
    "t_uint8",
    "t_uint16",
    "t_uint32",
    "t_sint8",
    "t_sint16",
    "t_sint32",
    "t_float32",
]
# CAUTION : Automatic generated code section: Start #

# CAUTION : Automatic generated code section: End #
def to_camel_case(name: str) -> str:
    return "".join(
        word.capitalize()
        for word in name.split("_")
    )
#------------------------------------------------------------------------------
#                                       CLASS
#------------------------------------------------------------------------------
class AppSpm_CodeGen():
    """Generate APP_SPM public/private configuration and typed client APIs."""

    code_gen = LCFE()

    @staticmethod
    def _is_empty(value) -> bool:
        return value in (None, 'None', '')

    @staticmethod
    def _specific_paths():
        """Resolve ConfigSpecific files from APP_SPM configuration root."""
        private_path = os.path.abspath(os.fspath(APPSPM_CFG_PRIVATE))
        app_cfg_root = os.path.dirname(os.path.dirname(private_path))

        specific_h = globals().get(
            "APPSPM_CFG_SPECIFIC_H",
            os.path.join(app_cfg_root, "ConfigSpecific", "APPSPM_ConfigSpecific.h")
        )
        specific_c = globals().get(
            "APPSPM_CFG_SPECIFIC_C",
            os.path.join(app_cfg_root, "ConfigSpecific", "APPSPM_ConfigSpecific.c")
        )

        return os.fspath(specific_h), os.fspath(specific_c)

    
    @staticmethod
    def _make_typed_api(item_cfg):

        name = str(item_cfg[APPSPM_COL_NAME]).upper()
        prm_type = str(item_cfg[APPSPM_COL_C_TYPE]).upper()
        prm_size = int(item_cfg[APPSPM_COL_SIZE])
        prm_access = str(item_cfg[APPSPM_COL_ACCESS]).upper()
        c_type = str(item_cfg[APPSPM_COL_C_TYPE])

        enum_name = f"{APPSPM_ENUM_ROOT_PARAM}_{name}"
        get_name = f"APPSPM_Get_{to_camel_case(name)}"
        set_name = f"APPSPM_Set_{to_camel_case(name)}"

        if prm_size <= 0:
            raise ValueError(
                f"APP_SPM parameter '{name}' has invalid size {prm_size}"
            )

        if prm_access not in ("RO", "WO", "RW"):
            raise ValueError(
                f"APP_SPM parameter '{name}' has invalid access policy "
                f"'{prm_access}'"
            )

        get_decl = ""
        get_impl = ""
        set_decl = ""
        set_impl = ""

        # ------------------------------------------------------------
        # STRING
        # ------------------------------------------------------------
        if prm_type == "T_CHAR":

            get_decl = (
                f"/** @brief Get parameter {name}. */\n"
                f"t_eReturnCode {get_name}"
                f"(t_char f_Value_ac[{prm_size}U]);\n\n"
            )

            get_impl = (
                f"/*********************************\n"
                f" * {get_name}\n"
                f" *********************************/\n"
                f"t_eReturnCode {get_name}"
                f"(t_char f_Value_ac[{prm_size}U])\n"
                f"{{\n"
                f"    return APPSPM_GetParam(\n"
                f"        {enum_name},\n"
                f"        (void *)f_Value_ac,\n"
                f"        (t_uint16){prm_size}U);\n"
                f"}}\n\n"
            )

            set_decl = (
                f"/** @brief Set parameter {name} from a "
                f"null-terminated string. */\n"
                f"t_eReturnCode {set_name}"
                f"(const t_char * f_Value_pc);\n\n"
            )

            set_impl = (
                f"/*********************************\n"
                f" * {set_name}\n"
                f" *********************************/\n"
                f"t_eReturnCode {set_name}"
                f"(const t_char * f_Value_pc)\n"
                f"{{\n"
                f"    t_eReturnCode Ret_e = RC_OK;\n"
                f"    t_char Value_ac[{prm_size}U] = {{0}};\n"
                f"    t_uint16 idx_u16 = 0U;\n\n"
                f"    if(f_Value_pc == NULL)\n"
                f"    {{\n"
                f"        Ret_e = RC_ERROR_PTR_NULL;\n"
                f"    }}\n"
                f"    else\n"
                f"    {{\n"
                f"        while((idx_u16 < "
                f"(t_uint16)({prm_size}U - 1U)) &&\n"
                f"              (f_Value_pc[idx_u16] != '\\0'))\n"
                f"        {{\n"
                f"            Value_ac[idx_u16] = "
                f"f_Value_pc[idx_u16];\n"
                f"            idx_u16++;\n"
                f"        }}\n\n"
                f"        Value_ac[idx_u16] = '\\0';\n"
                f"        Ret_e = APPSPM_SetParam(\n"
                f"            {enum_name},\n"
                f"            (const void *)Value_ac,\n"
                f"            (t_uint16){prm_size}U);\n"
                f"    }}\n\n"
                f"    return Ret_e;\n"
                f"}}\n\n"
            )

        # ------------------------------------------------------------
        # SCALAR
        # ------------------------------------------------------------
        elif c_type.lower() in APPSPM_SCALAR_C_TYPES:

            get_decl = (
                f"/** @brief Get parameter {name}. */\n"
                f"t_eReturnCode {get_name}"
                f"({c_type} * f_Value_p);\n\n"
            )

            get_impl = (
                f"/*********************************\n"
                f" * {get_name}\n"
                f" *********************************/\n"
                f"t_eReturnCode {get_name}"
                f"({c_type} * f_Value_p)\n"
                f"{{\n"
                f"    return APPSPM_GetParam(\n"
                f"        {enum_name},\n"
                f"        (void *)f_Value_p,\n"
                f"        (t_uint16)sizeof(*f_Value_p));\n"
                f"}}\n\n"
            )

            set_decl = (
                f"/** @brief Set parameter {name}. */\n"
                f"t_eReturnCode {set_name}"
                f"({c_type} f_Value);\n\n"
            )

            set_impl = (
                f"/*********************************\n"
                f" * {set_name}\n"
                f" *********************************/\n"
                f"t_eReturnCode {set_name}"
                f"({c_type} f_Value)\n"
                f"{{\n"
                f"    return APPSPM_SetParam(\n"
                f"        {enum_name},\n"
                f"        (const void *)&f_Value,\n"
                f"        (t_uint16)sizeof(f_Value));\n"
                f"}}\n\n"
            )

        # ------------------------------------------------------------
        # STRUCT / CUSTOM TYPE
        # ------------------------------------------------------------
        else:

            get_decl = (
                f"/** @brief Get parameter {name}. */\n"
                f"t_eReturnCode {get_name}"
                f"({c_type} * f_Value_p);\n\n"
            )

            get_impl = (
                f"_Static_assert(sizeof({c_type}) == {prm_size}U,\n"
                f"               \"APP_SPM size mismatch for {name}\");\n\n"
                f"/*********************************\n"
                f" * {get_name}\n"
                f" *********************************/\n"
                f"t_eReturnCode {get_name}"
                f"({c_type} * f_Value_p)\n"
                f"{{\n"
                f"    return APPSPM_GetParam(\n"
                f"        {enum_name},\n"
                f"        (void *)f_Value_p,\n"
                f"        (t_uint16)sizeof(*f_Value_p));\n"
                f"}}\n\n"
            )

            set_decl = (
                f"/** @brief Set parameter {name}. */\n"
                f"t_eReturnCode {set_name}"
                f"(const {c_type} * f_Value_p);\n\n"
            )

            set_impl = (
                f"/*********************************\n"
                f" * {set_name}\n"
                f" *********************************/\n"
                f"t_eReturnCode {set_name}"
                f"(const {c_type} * f_Value_p)\n"
                f"{{\n"
                f"    return APPSPM_SetParam(\n"
                f"        {enum_name},\n"
                f"        (const void *)f_Value_p,\n"
                f"        (t_uint16)sizeof(*f_Value_p));\n"
                f"}}\n\n"
            )

        # ------------------------------------------------------------
        # ACCESS POLICY
        # ------------------------------------------------------------
        if prm_access == "RO":
            decl = get_decl
            impl = get_impl

        elif prm_access == "WO":
            decl = set_decl
            impl = set_impl

        else:  # RW
            decl = get_decl + set_decl
            impl = get_impl + set_impl

        return decl, impl

    @classmethod
    def code_generation(cls, f_software_cfg, f_udscfg_path, f_is_uds_ope=False) -> None:
        item_prm_raw_a = None

        if isinstance(f_software_cfg, str) and os.path.isfile(f_software_cfg) and os.path.getsize(f_software_cfg) > 0:
            try:
                cls.code_gen.load_excel_file(f_software_cfg)
                item_prm_raw_a = cls.code_gen.get_array_from_excel("AppSpm_PrmInfo")
            except Exception as exc:
                print(
                    f"[WARNING] : APPSPM_Codegen -> invalid or unreadable config file "
                    f"'{f_software_cfg}', generate minimal code ({exc})"
                )
        else:
            print(
                f"[WARNING] : APPSPM_Codegen -> config file missing or empty "
                f"'{f_software_cfg}', generate minimal code"
            )

        item_prm_a = item_prm_raw_a[1:] if item_prm_raw_a is not None else []
        valid_item_prm_a = [
            prm_cfg for prm_cfg in item_prm_a
            if prm_cfg and len(prm_cfg) > APPSPM_COL_NAME and
            not cls._is_empty(prm_cfg[APPSPM_COL_NAME])
        ]

        enum_prm = ''
        var_prm = ''
        api_decl = ''
        api_impl = ''
        uds_item_prm = {'PARAMETERS': {}}

        #-----------------------------------------------------------------
        #-----------------------------make enum---------------------------
        #-----------------------------------------------------------------
        enum_names = [
            str(prm_cfg[APPSPM_COL_NAME]).upper()
            for prm_cfg in valid_item_prm_a
        ]
        enum_prm = cls.code_gen.make_enum_from_variable(
            APPSPM_ENUM_ROOT_PARAM,
            enum_names,
            't_eAPPSPM_ItemPrm',
            0,
            'Lists every system parameter.',
            []
        )

        #-----------------------------------------------------------------
        #---------------make exact-size caches + descriptors--------------
        #-----------------------------------------------------------------
        max_param_size = max(
            (int(item_cfg[APPSPM_COL_SIZE]) for item_cfg in valid_item_prm_a),
            default=1
        )

        if max_param_size <= 0:
            raise ValueError("APP_SPM maximum parameter size must be greater than zero")

        var_prm += (
            "    /// @brief Largest configured APP_SPM parameter in bytes.\n"
            f"    #define APPSPM_MAX_PARAM_SIZE ((t_uint16){max_param_size}U)\n\n"
        )

        for item_cfg in valid_item_prm_a:
            name = str(item_cfg[APPSPM_COL_NAME]).upper()
            prm_size = int(item_cfg[APPSPM_COL_SIZE])

            if prm_size <= 0 or prm_size > 0xFFFF:
                raise ValueError(
                    f"APP_SPM parameter '{name}' has invalid size {prm_size}; "
                    "expected 1..65535 bytes"
                )

            var_prm += (
                f"    /// @brief Exact-size RAM cache for parameter {name}.\n"
                f"    static t_uint8 g_APPSPM_{name}_Cache_au8[{prm_size}U];\n"
            )

        if valid_item_prm_a:
            var_prm += "\n"

        var_prm += (
            "    /// @brief Generated system parameter configuration.\n"
            f"    const t_sAPPSPM_ItemPrmCfg "
            f"c_AppSpm_ItemPrmInfo_as[{APPSPM_ENUM_ROOT_PARAM}_NB] = {{\n"
        )

        list_prm_type = []

        for item_cfg in valid_item_prm_a:
            name = str(item_cfg[APPSPM_COL_NAME]).upper()
            prm_type = str(item_cfg[APPSPM_COL_C_TYPE]).upper()
            prm_size = int(item_cfg[APPSPM_COL_SIZE])
            prm_access = str(item_cfg[APPSPM_COL_ACCESS]).upper()

            if prm_access not in ["RO", "RW", "WO"]:
                raise ValueError(f"UNdetermine Parameter Accessors --> {prm_access} for prm {name}")

            if cls._is_empty(item_cfg[APPSPM_COL_SIGNAL]):
                signal_related = "APPSIG_SIGNAL_NB"
            else:
                signal_name = str(item_cfg[APPSPM_COL_SIGNAL])
                if len(signal_name) > 32:
                    raise ValueError(
                        f"{signal_name} is too long, max is 32, get {len(signal_name)}"
                    )
                signal_related = f"APPSIG_SIGNAL_{signal_name}"

            if cls._is_empty(item_cfg[APPSPM_COL_NVM_OBJECT]):
                object_nvm_related = "FMKNVM_OBJECT_NB"
            else:
                object_nvm_related = f"FMKNVM_OBJECT_{item_cfg[APPSPM_COL_NVM_OBJECT]}"

            if prm_type.lower() not in APPSPM_SCALAR_C_TYPES:

                if prm_type == "T_CHAR": # string
                    prm_type = f"{prm_size}_{prm_type[2:]}"
                elif "T_S" in prm_type: # structure
                    prm_type = f"STRUCT_{prm_type[3:]}"

                if prm_type not in list_prm_type:
                    list_prm_type.append(prm_type)

                factor = "APPSPM_FACTOR_UNUSED"
                offset = "APPSPM_OFFSET_UNUSED"
                default = "APPSPM_DEFAULT_UNUSED"
                min_value = "APPSPM_MIN_UNUSED"
                max_value = "APPSPM_MAX_UNUSED"
            else:
                prm_type = f"{prm_type.upper()[2:]}"
                factor = item_cfg[APPSPM_COL_FACTOR]
                offset = item_cfg[APPSPM_COL_OFFSET]
                default = item_cfg[APPSPM_COL_DEFAULT]
                min_value = item_cfg[APPSPM_COL_MIN]
                max_value = item_cfg[APPSPM_COL_MAX]

            # Validate/infer the client C type now so bad custom configuration
            # is rejected during generation rather than during compilation.
            

            var_prm += (
                f"        [{APPSPM_ENUM_ROOT_PARAM}_{name}] = {{\n"
                f"            .version_u8 = (t_uint8){item_cfg[APPSPM_COL_VERSION]},\n"
                f"            .minItemVal_f32 = (t_float32){min_value},\n"
                f"            .maxItemVal_f32 = (t_float32){max_value},\n"
                f"            .DefaultItemVal_f32 = (t_float32){default},\n"
                f"            .factor_f32 = (t_float32){factor},\n"
                f"            .offset_s16 = (t_sint16){offset},\n"
                f"            .Type_e = {APPSPM_ENUM_ROOT_PRM_TYPE}_{prm_type},\n"
                f"            .Access_e = {APPSPM_ENUM_ROOT_ACESS}_{prm_access},\n"
                f"            .Size_u16 = (t_uint16){prm_size}U,\n"
                f"            .cacheData_pv = (void *)g_APPSPM_{name}_Cache_au8,\n"
                f"            .signal_e = {signal_related},\n"
                f"            .nvmObjectId_e = {object_nvm_related.upper()}\n"
                f"        }},\n"
            )

            decl, impl = cls._make_typed_api(item_cfg)
            api_decl += decl
            api_impl += impl

            if f_is_uds_ope:
                uds_item_prm["PARAMETERS"][name] = {
                    'id': f'{item_cfg[APPSPM_COL_ID]}',
                    'min': f'{int(item_cfg[APPSPM_COL_MIN])}',
                    'max': f'{int(item_cfg[APPSPM_COL_MAX])}',
                    'default': f'{int(item_cfg[APPSPM_COL_DEFAULT])}',
                    'machine': 0
                }

        var_prm += "    };\n\n"

        # make enum types 
        list_prm_type = list_prm_type + [
            old_prm_type.upper()[2:]
            for old_prm_type in APPSPM_SCALAR_C_TYPES
        ]
        enum_prm_type  = cls.code_gen.make_enum_from_variable(
                            APPSPM_ENUM_ROOT_PRM_TYPE,
                            list_prm_type,
                            't_eAPPSPM_PrmType',
                            0,
                            'Enumeration of type of parameter.',
                            []
                        )

        if f_is_uds_ope:
            with open(f_udscfg_path, "r", encoding="utf-8") as json_file:
                try:
                    existing_data = json.load(json_file)
                except json.JSONDecodeError:
                    existing_data = {}

            with open(f_udscfg_path, "w", encoding="utf-8") as json_file:
                existing_data.update(uds_item_prm)
                json.dump(existing_data, json_file, indent=4, ensure_ascii=False)

        specific_h_path, specific_c_path = cls._specific_paths()

        #-----------------------------------------------------------------
        #------------------------make code gen----------------------------
        #-----------------------------------------------------------------
        print('[INFO] : APPSPM_Codegen -> Config Public Code Generation')
        cls.code_gen.change_target_balise(
            TARGET_T_ENUM_START_LINE,
            TARGET_T_ENUM_END_LINE
        )
        cls.code_gen._write_into_file(enum_prm, APPSPM_CFG_PUBLIC)
        cls.code_gen._write_into_file(enum_prm_type, APPSPM_CFG_PUBLIC)

        print('[INFO] : APPSPM_Codegen -> Config Private Code Generation')
        cls.code_gen.change_target_balise(
            TARGET_T_VARIABLE_START_LINE,
            TARGET_T_VARIABLE_END_LINE
        )
        cls.code_gen._write_into_file(var_prm, APPSPM_CFG_PRIVATE)

        print('[INFO] : APPSPM_Codegen -> Config Specific API Declaration Generation')
        cls.code_gen.change_target_balise(
            TARGET_T_PARAM_API_DECL_START_LINE,
            TARGET_T_PARAM_API_DECL_END_LINE
        )
        cls.code_gen._write_into_file(api_decl, specific_h_path)

        print('[INFO] : APPSPM_Codegen -> Config Specific API Implementation Generation')
        cls.code_gen.change_target_balise(
            TARGET_T_PARAM_API_IMPL_START_LINE,
            TARGET_T_PARAM_API_IMPL_END_LINE
        )
        cls.code_gen._write_into_file(api_impl, specific_c_path)

#------------------------------------------------------------------------------
#                              END OF FILE
#------------------------------------------------------------------------------
