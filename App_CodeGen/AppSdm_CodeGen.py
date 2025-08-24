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

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from PythonToolCfg.APP_PATH import *
import json
import shutil
from .AppLgc_CodeGen import APPLGC_ENUM_SRV
from PyCodeGene import LoadConfig_FromExcel as LCFE, TARGET_T_END_LINE,TARGET_T_ENUM_END_LINE, \
                                                    TARGET_T_ENUM_START_LINE,TARGET_T_START_LINE,TARGET_T_VARIABLE_START_LINE,\
                                                    TARGET_T_VARIABLE_END_LINE,TARGET_T_STRUCT_START_LINE,\
                                                    TARGET_T_STRUCT_END_LINE,TARGET_T_INCLUDE_START, TARGET_T_INCLUDE_END
#------------------------------------------------------------------------------
#                                       CONSTANT
#------------------------------------------------------------------------------
APPSDM_ENUM_ROOT_DIAG_ITEM = "APPSDM_DIAG_ITEM"
APPSDM_ENM_DIAG_STRAT = "APPSDM_DIAG_STRAT"

TARGET_T_DIAG_STRAT_DECL_START_LINE = "    /* CAUTION : Automatic generated code section for Diag Strategy Function Declaration: Start */\n"
TARGET_T_DIAG_STRAT_DECL_END_LINE =   "    /* CAUTION : Automatic generated code section for Diag Strategy Function Declaration: End */\n"
TARGET_T_DIAG_STRAT_IMPL_START_LINE = "/* CAUTION : Automatic generated code section for Diag Strategy Function Implementation: Start */\n"
TARGET_T_DIAG_STRAT_IMPL_END_LINE =   "/* CAUTION : Automatic generated code section for Diag Strategy Function Implementation: End */\n"
# CAUTION : Automatic generated code section: Start #

# CAUTION : Automatic generated code section: End #
#------------------------------------------------------------------------------
#                                       CLASS
#------------------------------------------------------------------------------
class AppSdm_CodeGen():
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
    def code_generation(cls, f_software_cfg, f_udscfg_path, f_is_uds_ope=False) -> None:
        # Load needed excel arrays
        cls.code_gen.load_excel_file(f_software_cfg)
        items_cfg_a = cls.code_gen.get_array_from_excel("AppSdm_DiagItemInfo")[1:]
        strat_func_a = cls.code_gen.get_array_from_excel("AppSdm_ItemDiag")[1:]

        # make python varaible 
        enum_item = ""
        enum_strat = ""
        var_item_info = ""
        var_strat_cb = ""

        decl_strat_func = ""
        impl_strat_func = ""
        uds_sdm_data = {}
        uds_sdm_data["DIAGNOSTIC"] = {}
        #-----------------------------------------------------------------
        #-----------------------------make all enum-----------------------
        #-----------------------------------------------------------------
        enum_item += "    /**\n" + "    * @brief Enum Diagnostic Item\n" + "    */\n"\
                    + "    typedef enum ____t_eAPPSDM_DiagnosticItem\n"\
                    + "    {\n"
        var_item_info += "    /**\n" + "    * @brief Diagnostic Item Configuration\n" + "    */\n"\
                    + f'    t_sAPPSM_DiagItemCfg c_AppSdm_DiagItemCfg_as[{APPSDM_ENUM_ROOT_DIAG_ITEM}_NB] =' + '{\n'\
                    + '        // DebuncerCounter              Unactive Item Delay          NotifyUser                     Log Error                      Applied Startegy\n'
        for idx, item_info in enumerate(items_cfg_a):
            if idx == 0:
                enum_item += f'        {APPSDM_ENUM_ROOT_DIAG_ITEM}_{str(item_info[1]).upper()} = 0x00,'
            else:
                enum_item += f'        {APPSDM_ENUM_ROOT_DIAG_ITEM}_{str(item_info[1]).upper()},'

            enum_item += " " * ((SPACE_VARIABLE) - len(f"{APPSDM_ENUM_ROOT_DIAG_ITEM}_{item_info[1]}"))\
                        + f'// {str(item_info[-1])}\n'
            
            if item_info[3] is None:
                stay_unactive_delay = '0xFFFFFFFF'
            else:
                stay_unactive_delay = item_info[3]
            var_item_info += '        {'\
                        + f'(t_uint16){item_info[2]},'\
                        + " " * ((SPACE_VARIABLE) - len(f"(t_uint16){item_info[2]},"))\
                        + f'(t_uint32){stay_unactive_delay},'\
                        + " " * ((SPACE_VARIABLE) - len(f"(t_uint32){stay_unactive_delay},"))\
                        + f'(t_bool){item_info[4]},'\
                        + " " * ((SPACE_VARIABLE) - len(f"(t_bool){item_info[4]},"))\
                        + f'(t_bool){item_info[5]},'\
                        + " " * ((SPACE_VARIABLE) - len(f"(t_bool){item_info[5]},"))
            if str(item_info[5]) == 'None':
                var_item_info += f'{APPSDM_ENM_DIAG_STRAT}_NONE'
            else:
                var_item_info += f'{APPSDM_ENM_DIAG_STRAT}_{str(item_info[6]).upper()}'

            var_item_info += '},'\
                            + " " * ((SPACE_VARIABLE) - len(f"{APPSDM_ENM_DIAG_STRAT}_{str(item_info[6])}"))\
                            + f'// {item_info[1]}\n'
            
            if f_is_uds_ope:
                    uds_sdm_data["DIAGNOSTIC"][str(item_info[1])] = {
                            'id' : f'{idx}',
                            'debug_Info_1' : f'{str(item_info[7])}',
                            'debug_Info_2' : f'{str(item_info[8])}'
                    }
        
        enum_item += f'\n        {APPSDM_ENUM_ROOT_DIAG_ITEM}_NB,\n'
        enum_item += '    } t_eAPPSDM_DiagnosticItem;\n'
        var_item_info += '    };\n\n'
        
        if f_is_uds_ope:
            with open(f_udscfg_path, "r", encoding="utf-8") as json_file:
                try:
                    existing_data = json.load(json_file)
                except json.JSONDecodeError:
                    existing_data = {}
            with open(f_udscfg_path, "w", encoding="utf-8") as json_file:
                existing_data.update(uds_sdm_data)
                json.dump(existing_data, json_file, indent=4, ensure_ascii=False)
    
        #-----------------------------------------------------------------
        #------------------------make Strategy-----------------------------
        #-----------------------------------------------------------------
        var_strat_cb += "    /**\n" + "    * @brief Diagnostic Item Configuration\n" + "    */\n"\
                    + f'    t_cbAPPSDM_AppliedDiagStrategy * c_AppSdm_DiagStragies_apf[{APPSDM_ENM_DIAG_STRAT}_NB]' + '= {\n'
        enum_strat += "    /**\n" + "    * @brief Enum Diagnostic Strategy\n" + "    */\n"\
                    + "    typedef enum ____t_eAPPSDM_DiagnosticStrat\n"\
                    + "    {\n"
        for idx, strat_info in enumerate(strat_func_a):
            if strat_info[0] != None:
                if idx == 0:
                    enum_strat += f'        {APPSDM_ENM_DIAG_STRAT}_{str(strat_info[0]).upper()} = 0x00,'
                else:
                    enum_strat += f'        {APPSDM_ENM_DIAG_STRAT}_{str(strat_info[0]).upper()},'

                enum_strat += " " * ((SPACE_VARIABLE) - len(f"{APPSDM_ENUM_ROOT_DIAG_ITEM}_{strat_info[0]}"))\
                            + f'// {str(strat_info[-1])}\n'

                var_strat_cb += f'        APPSDM_SPEC_DiagStrat_{str(strat_info[0])},\n'

                decl_strat_func +=  "    /**\n" + f"    * @brief Stratefy Function : {strat_info[1]}\n" + "    */\n"\
                    + f'    void APPSDM_SPEC_DiagStrat_{str(strat_info[0])}(t_eAPPSDM_DiagStratOpe f_stratOpe_e);\n\n'
                
                impl_strat_func += AppSdm_CodeGen.make_diag_strat_impl(strat_info)
        var_strat_cb += '    };\n\n'

        enum_strat += f'\n        {APPSDM_ENM_DIAG_STRAT}_NB,\n'
        enum_strat += f'\n        {APPSDM_ENM_DIAG_STRAT}_NONE,\n'
        enum_strat += '    } t_eAPPSDM_DiagnosticStrat;\n'

        
        #-----------------------------------------------------------------
        #------------------------make drivers-----------------------------
        #-----------------------------------------------------------------
       
        #-----------------------------------------------------------------
        #------------------------make code gen----------------------------
        #-----------------------------------------------------------------
        print('[INFO] : APPSDM_Codegen -> Config Public Code Generation')
        cls.code_gen.change_target_balise(TARGET_T_ENUM_START_LINE,TARGET_T_ENUM_END_LINE)
        cls.code_gen._write_into_file(enum_strat, APPSDM_CONFIGPUBLIC_PATH)
        cls.code_gen._write_into_file(enum_item, APPSDM_CONFIGPUBLIC_PATH)

        
        print('[INFO] : APPSDM_Codegen -> Config Private Code Generation')
        cls.code_gen.change_target_balise(TARGET_T_VARIABLE_START_LINE,TARGET_T_VARIABLE_END_LINE)
        cls.code_gen._write_into_file(var_item_info, APPSDM_CONFIGPRIVATE_PATH)
        cls.code_gen._write_into_file(var_strat_cb, APPSDM_CONFIGPRIVATE_PATH)

        print('[INFO] : APPSDM_Codegen -> Config Specific Code Generation')
        cls.code_gen.change_target_balise(TARGET_T_DIAG_STRAT_DECL_START_LINE, TARGET_T_DIAG_STRAT_DECL_END_LINE)
        cls.code_gen._write_into_file(decl_strat_func, APPSDM_CONGSPECIFIC_H)

        cls.code_gen.change_target_balise(TARGET_T_DIAG_STRAT_IMPL_START_LINE, TARGET_T_DIAG_STRAT_IMPL_END_LINE)
        cls.code_gen._write_into_file(impl_strat_func, APPSDM_CONGSPECIFIC_C)

        
        
    @classmethod
    def make_diag_strat_impl(self, f_strat_info):
        retval = ''
        retval += '/*********************************\n'\
                + f'APPSDM_SPEC_DiagStrat_{str(f_strat_info[0])}\n'\
                + ' *********************************/\n'
        retval +=  f'void APPSDM_SPEC_DiagStrat_{str(f_strat_info[0])}(t_eAPPSDM_DiagStratOpe f_stratOpe_e)\n' + '{\n'\
                + '    t_eAPPLGC_SrvHealth srvHealth_e;\n'\
                + '    t_eReturnCode Ret_e = RC_OK;\n\n'\
                + '    Ret_e = s_APPSDM_SPEC_GetHealthFromStratOpe(f_stratOpe_e, &srvHealth_e);\n\n'\
                
        for srv_implied in f_strat_info[2:]:
            if str(srv_implied) != 'None':
                retval +='    if(Ret_e == RC_OK)\n'\
                        + '    {\n'\
                        + f'        Ret_e = APPLGC_SetServiceHealth({APPLGC_ENUM_SRV}_{str(srv_implied).upper()}, srvHealth_e);\n'\
                        + '    }\n'
        retval += '\n' + '    return;\n' + '}\n\n'
        return retval
                

        
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

