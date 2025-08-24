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
class AppSys_CodeGen():
    """
        Make code generation for FMKCDA module which include 
        file FMKSDM_ConfigPublic.h : 
            - enum machine
            - enum option list
            - enum for each option list value 
            - variable for cfg machine             
        
        file FMKSDM_ConfigPrivate.h :
            - variable for item diagnostic info 
            - varaible Strategy Applied Function

    """
    code_gen = LCFE()

    @classmethod
    def code_generation(cls, f_software_cfg, f_udscfg_path, f_is_uds_ope= False) -> None:
        # Load needed excel arrays
        cls.code_gen.load_excel_file(f_software_cfg)


        list_enm_option_value = []
        enm_opt_id_list = ""
        var_mach_info = ""
        enm_mach_list = ''
        var_prm_opt = ''
        option_list_a = cls.code_gen.get_array_from_excel("APPSYS_SysOptListEnum")[1:]
        cfg_machine_a = cls.code_gen.get_array_from_excel("APPSYS_CfgMachine")

        optiont_list_id = []
        optiont_list_desc = []
        option_values = []
        var_prm_opt += '    ///@brief Variable to get/set the machine configuration\n'\
                        + '    const t_eAPPSPM_ItemPrm c_AppSys_SysOpt_ItemPrmID_ae[APPSYS_OPT_ID_NB] = {\n'
        for option_info in option_list_a:
            optiont_list_id.append(option_info[0])
            var_prm_opt += f'        APPSPM_PRM_SYS_OPT_{option_info[0]},'\
                        + ' ' * (50 - len(f"APPSPM_PRM_SYS_OPT_{option_info[0]}"))\
                        + f'// APPSYS_OPT_ID_{option_info[0]}\n'
            
            optiont_list_desc.append(f"Enum for Option Description for {str(option_info[0]).capitalize()}")
            option_values.append(f"UNUSED")
            for value in option_info[1:]:
                if value != None and str(value) != 'None':
                    option_values.append(f"{value}")

            
            opt_id = cls.to_camel_case(str(option_info[0]))
            list_enm_option_value.append(cls.code_gen.make_enum_from_variable(f"APPSYS_OPT_{option_info[0].upper()}", 
                                                                    option_values, f"t_eAPPSYS_Opt{opt_id}",0,
                                                                    f"Enum Option list for  {option_info[0].upper()}"))
            option_values = []

        enm_opt_id_list = cls.code_gen.make_enum_from_variable("APPSYS_OPT_ID", 
                                                                optiont_list_id, "t_eAPPSYS_SysOptionList", 0,
                                                                "System Option List")
        
        machine_list = []
        var_mach_info = "    ///@brief Machine Option Configuration\n"\
                    + "    const t_uint8 c_AppSys_MachOptCfg_ua8[APPSYS_MACHINE_NB][APPSYS_OPT_ID_NB] = {\n"
        for machine_info in cfg_machine_a[1:]:
            machine_list.append(str(machine_info[0]).upper())

            var_mach_info += '        {'
            for idx, opt_value in enumerate(machine_info[1:]):
                var_mach_info += f"APPSYS_OPT_{str(cfg_machine_a[0][idx+1]).upper()}_{opt_value.upper()},"\
                            + ' ' * (50 - len(f"APPSYS_OPT_{str(cfg_machine_a[0][idx+1]).upper()}_{opt_value.upper()}"))

            var_mach_info += '},' + f'  // APPSYS_MACHINE_{str(machine_info[0]).upper()}\n'
        var_prm_opt += '    };\n\n'
        var_mach_info += '    };\n\n'
        enm_mach_list = cls.code_gen.make_enum_from_variable("APPSYS_MACHINE", machine_list, "t_eAPPSYS_MachineList", 0)
        #-----------------------------------------------------------------
        #-----------------------------make all enum-----------------------
        #-----------------------------------------------------------------
       
        #-----------------------------------------------------------------
        #------------------------make code gen----------------------------
        #-----------------------------------------------------------------
        print('[INFO] : APPSYS_Codegen -> Config Public Code Generation')
        cls.code_gen.change_target_balise(TARGET_T_ENUM_START_LINE, TARGET_T_ENUM_END_LINE)
        cls.code_gen._write_into_file(enm_opt_id_list, APPSYS_CFG_PUBLIC)
        for enm_opt_value in list_enm_option_value:
            cls.code_gen._write_into_file(enm_opt_value, APPSYS_CFG_PUBLIC)
        cls.code_gen._write_into_file(enm_mach_list, APPSYS_CFG_PUBLIC)

        print('[INFO] : APPSYS_Codegen -> Config Private Code Generation')
        cls.code_gen.change_target_balise(TARGET_T_VARIABLE_START_LINE, TARGET_T_VARIABLE_END_LINE)
        cls.code_gen._write_into_file(var_prm_opt, APPSYS_CFG_PRIVATE)
        cls.code_gen._write_into_file(var_mach_info, APPSYS_CFG_PRIVATE)


    @classmethod
    def to_camel_case(cls, name: str) -> str:
        parts = name.lower().split('_')   # sépare et met en minuscules
        return ''.join(word.capitalize() for word in parts)
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

