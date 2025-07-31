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
    def code_generation(cls, f_software_cfg, f_udscfg_path, f_is_uds_ope) -> None:
        # Load needed excel arrays
        cls.code_gen.load_excel_file(f_software_cfg)

        item_prm_a = cls.code_gen.get_array_from_excel("AppSpm_PrmInfo")[1:]
        enum_prm = ''
        var_prm = ''
        uds_item_prm = {}
        uds_item_prm['PARAMETERS'] = {}
        #-----------------------------------------------------------------
        #-----------------------------make all enum-----------------------
        #-----------------------------------------------------------------
        if str(item_prm_a[0][0] != EMPTY_CELL):
            enum_prm = cls.code_gen.make_enum_from_variable(APPSPM_ENUM_ROOT_PARAM, [str(prm_cfg[1]).upper() for prm_cfg in item_prm_a],
                                                            't_eAPPSPM_ItemPrm', 0, 'Enum for listong every parameter',
                                                            [])
        else : 
            enum_prm = cls.code_gen.make_enum_from_variable(APPSPM_ENUM_ROOT_PARAM, [],
                                                                "t_eAPPSPM_ItemPrm", 0, "Enum for listong every parameter",
                                                                [])
        
        var_prm += "    /**< Variable for System Parameter Inforamtion*/\n" \
                    + f"    const t_sAPPSPM_ItemPrmCfg c_AppSpm_ItemPrmInfo_as[{APPSPM_ENUM_ROOT_PARAM}_NB] =" + "{\n"
        var_prm += '    //itemId_u8                     version_u8                   minItemVal_u16                maxItemVal_u16                 DefaultItemVal_u16\n'
        for item_cfg in item_prm_a:
            var_prm += '    {' + f'(t_uint8){item_cfg[0]},'\
                    + " " * ((SPACE_VARIABLE) - len(f"(t_uint8){item_cfg[0]}"))\
                    + f'(t_uint8){item_cfg[2]},'\
                    + " " * ((SPACE_VARIABLE) - len(f"(t_uint8){item_cfg[2]}"))\
                    + f'(t_uint16){item_cfg[3]},'\
                    + " " * ((SPACE_VARIABLE) - len(f"(t_uint16){item_cfg[3]}"))\
                    + f'(t_uint16){item_cfg[4]},'\
                    + " " * ((SPACE_VARIABLE) - len(f"(t_uint16){item_cfg[4]}"))\
                    + f'(t_uint16){item_cfg[5]}' + '},\n'
            if f_is_uds_ope:
                uds_item_prm["PARAMETERS"][str(item_cfg[1]).upper()] = {
                        'id' : f'{item_cfg[0]}',
                        'min' : f'{int(item_cfg[3])}',
                        'max' : f'{int(item_cfg[4])}',
                        'default' : f'{int(item_cfg[5])}',
                        'machine' : 0
                }
            
        var_prm += '    };\n'
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

