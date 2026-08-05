"""
#  @file        main.py
#  @brief       Template_BriefDescription.
#  @details     TemplateDetailsDescription.\n
#
#  @author      mba
#  @date        jj/mm/yyyy
#  @version     1.0
"""
#------------------------------------------------------------------------------
#                                       IMPORT
#------------------------------------------------------------------------------

import sys
import os

# Chemin absolu vers le dossier parent
current_dir = os.path.dirname(__file__)
root_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))  # remonte jusqu'à Doc\ConfigPrj\PythonTool_CodeGen

from PythonToolCfg.APP_PATH import *
import os, json

from .AppLgc_CodeGen import APPLGC_ENUM_SRV
from PyCodeGene import LoadConfig_FromExcel as LCFE, TARGET_T_END_LINE,TARGET_T_ENUM_END_LINE, \
                                                    TARGET_T_ENUM_START_LINE,TARGET_T_START_LINE,TARGET_T_VARIABLE_START_LINE,\
                                                    TARGET_T_VARIABLE_END_LINE,TARGET_T_STRUCT_START_LINE,\
                                                    TARGET_T_STRUCT_END_LINE,TARGET_T_INCLUDE_START, TARGET_T_INCLUDE_END
#------------------------------------------------------------------------------
#                                       CONSTANT
#------------------------------------------------------------------------------
APPSPM_ENUM_ROOT_PARAM= "APPSPM_PRM"

TARGET_T_DIAG_STRAT_DECL_START_LINE = "    /* CAUTION : Automatic generated code section for Diag Strategy Function Declaration: Start */\n"
TARGET_T_DIAG_STRAT_DECL_END_LINE =   "    /* CAUTION : Automatic generated code section for Diag Strategy Function Declaration: End */\n"
TARGET_T_DIAG_STRAT_IMPL_START_LINE = "/* CAUTION : Automatic generated code section for Diag Strategy Function Implementation: Start */\n"
TARGET_T_DIAG_STRAT_IMPL_END_LINE =   "/* CAUTION : Automatic generated code section for Diag Strategy Function Implementation: End */\n"
# CAUTION : Automatic generated code section: Start #

# CAUTION : Automatic generated code section: End #
#------------------------------------------------------------------------------
#                                       CLASS
#------------------------------------------------------------------------------
class AppSpm_CodeGen():
    """
        Make code generation for FMKCDA module which include 
        file FMKSDM_ConfigPublic.h : 
            - Enum Item
            - Enum Strategy              
        
        file FMKSDM_ConfigPrivate.h :
            - variable for item diagnostic info 
            - varaible Strategy Applied Function

    """
    code_gen = LCFE()

    @classmethod
    def code_generation(cls, f_software_cfg, f_udscfg_path, f_is_uds_ope= False) -> None:
        item_prm_raw_a = None
        if isinstance(f_software_cfg, str) and os.path.isfile(f_software_cfg) and os.path.getsize(f_software_cfg) > 0:
            try:
                cls.code_gen.load_excel_file(f_software_cfg)
                item_prm_raw_a = cls.code_gen.get_array_from_excel("AppSpm_PrmInfo")
            except Exception as exc:
                print(f"[WARNING] : APPSPM_Codegen -> invalid or unreadable config file '{f_software_cfg}', generate minimal code ({exc})")
        else:
            print(f"[WARNING] : APPSPM_Codegen -> config file missing or empty '{f_software_cfg}', generate minimal code")

        item_prm_a = item_prm_raw_a[1:] if item_prm_raw_a is not None else []
        valid_item_prm_a = [prm_cfg for prm_cfg in item_prm_a if prm_cfg and len(prm_cfg) > 1 and prm_cfg[1] not in (None, 'None', '')]
        enum_prm = ''
        var_prm = ''
        uds_item_prm = {}
        uds_item_prm['PARAMETERS'] = {}
        #-----------------------------------------------------------------
        #-----------------------------make all enum-----------------------
        #-----------------------------------------------------------------
        if valid_item_prm_a != []:
            enum_prm = cls.code_gen.make_enum_from_variable(APPSPM_ENUM_ROOT_PARAM, [str(prm_cfg[1]).upper() for prm_cfg in valid_item_prm_a],
                                                            't_eAPPSPM_ItemPrm', 0, 'Enum for listong every parameter',
                                                            [])
        else : 
            enum_prm = cls.code_gen.make_enum_from_variable(APPSPM_ENUM_ROOT_PARAM, [],
                                                                "t_eAPPSPM_ItemPrm", 0, "Enum for listong every parameter",
                                                                [])
        var_prm += "    ///@brief Variable for System Parameter Inforamtion\n" \
                    + f"    const t_sAPPSPM_ItemPrmCfg c_AppSpm_ItemPrmInfo_as[{APPSPM_ENUM_ROOT_PARAM}_NB] =" + "{\n"
        var_prm += '    //version_u8                   minItemVal_u16                maxItemVal_u16                 DefaultItemVal_u16\n'
        for item_cfg in valid_item_prm_a:
            if item_cfg[9] is None:
                signal_related = "APPSIG_SIGNAL_NB"
            else: 
                if len(item_cfg[9]) > 32:
                    raise ValueError(f'{item_cfg[9]} is too long, max is 32, get {len(item_cfg[9])}')
                signal_related = f"APPSIG_SIGNAL_{item_cfg[9]}"

            var_prm += f'    [{APPSPM_ENUM_ROOT_PARAM}_{item_cfg[1]}] = ' + '{\n'\
                    + f'        .version_u8 = (t_uint8){item_cfg[2]},\n'\
                    + f'        .minItemVal_f32 = (t_float32){item_cfg[3]},\n'\
                    + f'        .maxItemVal_f32 = (t_float32){item_cfg[4]},\n'\
                    + f'        .DefaultItemVal_f32 = (t_float32){item_cfg[5]},\n'\
                    + f'        .factor_f32 = (t_float32){item_cfg[7]},\n'\
                    + f'        .offset_s16 = (t_sint16){item_cfg[8]},\n'\
                    + f'        .prmType_e = APPSPM_PRM_TYPE_{str(item_cfg[6]).upper()},\n'\
                    + f'        .signal_e = {signal_related}\n'\
                    +  '    },\n'
            
            if f_is_uds_ope:
                uds_item_prm["PARAMETERS"][str(item_cfg[1]).upper()] = {
                        'id' : f'{item_cfg[0]}',
                        'min' : f'{int(item_cfg[3])}',
                        'max' : f'{int(item_cfg[4])}',
                        'default' : f'{int(item_cfg[5])}',
                        'machine' : 0
                }
        var_prm += '    };\n\n\n'

        if f_is_uds_ope:
            with open(f_udscfg_path, "r", encoding="utf-8") as json_file:
                try:
                    existing_data = json.load(json_file)
                except json.JSONDecodeError:
                    existing_data = {}
            with open(f_udscfg_path, "w", encoding="utf-8") as json_file:
                existing_data.update(uds_item_prm)
                json.dump(existing_data, json_file, indent=4, ensure_ascii=False)

        # uds cfg 
                

        #-----------------------------------------------------------------
        #------------------------make code gen----------------------------
        #-----------------------------------------------------------------
        print('[INFO] : APPSPM_Codegen -> Config Public Code Generation')
        cls.code_gen.change_target_balise(TARGET_T_ENUM_START_LINE,TARGET_T_ENUM_END_LINE)
        cls.code_gen._write_into_file(enum_prm, APPSPM_CFG_PUBLIC)

        print('[INFO] : APPSPM_Codegen -> Config Private Code Generation')
        cls.code_gen.change_target_balise(TARGET_T_VARIABLE_START_LINE,TARGET_T_VARIABLE_END_LINE)
        cls.code_gen._write_into_file(var_prm, APPSPM_CFG_PRIVATE)

        
#------------------------------------------------------------------------------
#                             FUNCTION IMPLMENTATION
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
#			                MAIN
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
#		                    END OF FILE
#------------------------------------------------------------------------------
#--------------------------
# Function_name
#--------------------------

"""
    @brief
    @details

    @params[in]
    @params[out]
    @retval
"""

