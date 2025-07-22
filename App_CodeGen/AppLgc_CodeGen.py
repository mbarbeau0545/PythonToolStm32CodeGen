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
import os, json
import shutil
from PyCodeGene import LoadConfig_FromExcel as LCFE, TARGET_T_END_LINE,TARGET_T_ENUM_END_LINE, \
                                                    TARGET_T_ENUM_START_LINE,TARGET_T_VARIABLE_START_LINE,\
                                                    TARGET_T_VARIABLE_END_LINE, TARGET_VARIABLE_END_LINE,TARGET_VARIABLE_START_LINE
#------------------------------------------------------------------------------
#                                       CONSTANT
#------------------------------------------------------------------------------
APPLGC_ENUM_AGENT = "APPLGC_AGENT"
APPLGC_ENUM_SRV = "APPLGC_SRV"

TARGET_ASSP_SRV_ACT_VALUE_START = "    /* CAUTION : Automatic generated code section for Actuators Containers/Service: Start */\n"
TARGET_ASSP_SRV_ACT_VALUE_END   = "    /* CAUTION : Automatic generated code section for Actuators Containers/Service: End */\n"
# CAUTION : Automatic generated code section: Start #

# CAUTION : Automatic generated code section: End #
#------------------------------------------------------------------------------
#                                       CLASS
#------------------------------------------------------------------------------
class AppLgc_CodeGen():
    """
        Make code generation for FMKCDA module which include 
        file APPLGC_ConfigPublic.h : 
            - Enum Item
            - Enum Strategy              
        
        file APPLGC_ConfigPrivate.h :
            - variable for item diagnostic info 
            - varaible Strategy Applied Function

    """
    code_gen = LCFE()

    @classmethod
    def code_generation(cls, f_software_cfg, f_udscfg_path, f_is_uds_ope) -> None:
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("<<<<<<<<<<<<<<<<<<<<Start code generation for AppAct Module>>>>>>>>>>>>>>>>>>>")
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

        # Load needed
        cls.code_gen.load_excel_file(f_software_cfg)
        agent_cfg_a = cls.code_gen.get_array_from_excel("AppLgc_Agent")[1:]
        service_cfg_a = cls.code_gen.get_array_from_excel("AppLgc_Srv")[1:]

        # make python varaible 
        enum_agent = ""
        var_agent = ""
        enum_srv = ""
        decl_srv_val_container = ""
        var_act_srv_asso = ""
        var_max_act_value = ""

        enm_dependencies = ""
        var_depencies = ""
        var_srv_dependencies = ""
        var_depencies_value = ""
        uds_lgc_data = {}
        uds_lgc_data["LOGIC"] = {}
        uds_lgc_data["LOGIC"]["SERVICE"] = {}
        uds_lgc_data["LOGIC"]["AGENTS"] = {}
        #-----------------------------------------------------------------
        #-----------------------------make all enum-----------------------
        #-----------------------------------------------------------------
        enum_agent += "    /**\n" + "    * @brief Enum for Agent\n" + "    */\n"\
                    + "    typedef enum ____t_eAPPLGC_AgentList\n"\
                    + "    {\n"

        var_agent += "    /**\n" + "    * @brief Agent Configuration Function\n" + "    */\n"\
                    + f'    const t_sAPPLGC_AgentFunc c_AppLGc_AgentFunc_apf[{APPLGC_ENUM_AGENT}_NB] =' + '{\n'
        
        for idx_agt, agent_info in enumerate(agent_cfg_a):
            if str(agent_info[0]) != 'None':
                if idx_agt == 0:
                    enum_agent += f'        {APPLGC_ENUM_AGENT}_{str(agent_info[0]).upper()} = 0x00,'
                else:
                    enum_agent += f'        {APPLGC_ENUM_AGENT}_{str(agent_info[0]).upper()},'

                enum_agent += " " * ((SPACE_VARIABLE) - len(f"{APPLGC_ENUM_AGENT}_{str(agent_info[0]).upper()},"))\
                            + f'// {str(agent_info[-1])}\n'
                
                var_agent += '        {'\
                            + f'{agent_info[0]}_Init,'\
                            + " " * ((SPACE_VARIABLE) - len(f"{agent_info[0]},"))\
                            + f'{agent_info[0]}_Cyclic'\
                            + '},' + f'// {APPLGC_ENUM_AGENT}_{str(agent_info[0]).upper()}\n'

                if f_is_uds_ope:
                    uds_lgc_data["LOGIC"]["AGENTS"][str(agent_info[0]).upper()] = {
                            'id' : f'{idx_agt}',
                            'description' : f'{agent_info[-1]}'
                    }


        
        enum_agent += f'\n        {APPLGC_ENUM_AGENT}_NB,\n'
        enum_agent += '    } t_eAPPLGC_AgentList;\n'
        var_agent += '    };\n\n'
        
    
        #-----------------------------------------------------------------
        #------------------------make Strategy-----------------------------
        #-----------------------------------------------------------------
        enum_srv += "    /**\n" + "    * @brief Enum for Service Function Listy\n" + "    */\n"\
                    + "    typedef enum ____t_eAPPLGC_SrvList\n"\
                    + "    {\n"
        var_srv_dependencies  += "    /**\n" + "    * @brief Service Actuators Variable Mapping\n" + "    */\n"\
                                + f'    const t_eAPPACT_Actuators * c_AppLGc_SrvDepedencies_pae[{APPLGC_ENUM_SRV}_NB] =' + '{\n'
        
        var_max_act_value  += "    /**\n" + "    * @brief Service Max Actuators values \n" + "    */\n"\
                                + f'    const t_uint8 c_AppLGc_SrvActuatorsMax_ua8[{APPLGC_ENUM_SRV}_NB] =' + ' {\n'
        for idx_srv, service_cfg in enumerate(service_cfg_a):
            if str(service_cfg[0]) != 'None':
                if idx_srv == 0:
                    enum_srv += f'        {APPLGC_ENUM_SRV}_{str(service_cfg[0]).upper()} = 0x00,\n'
                else:
                    enum_srv += f'        {APPLGC_ENUM_SRV}_{str(service_cfg[0]).upper()},\n'

                enm_dependencies += "    /**\n" + f"    * @brief Enum for Service {service_cfg[0]}\n" + "    */\n"\
                        + f"    typedef enum ____t_eAPPLGC_Srv{service_cfg[0]}\n"\
                        + "    {\n"
                
                var_depencies += "    /**\n" + f"    * @brief Variable for Actuators/Service Mapping\n" + "    */\n"\
                        + f'        const t_eAPPACT_Actuators c_AppLgc_ActService{service_cfg[0]}Mapp_ae[APPLGC_{str(service_cfg[0]).upper()}_ACT_NB]' + '= {\n'

                decl_srv_val_container +=  "/**\n" + f"* @brief Actuators Values Containers for {service_cfg[0]}\n" + "*/\n"\
                        + f'static t_uAPPACT_SetValue g_ActContainer{service_cfg[0]}_au[APPLGC_{str(service_cfg[0]).upper()}_ACT_NB];\n\n'
            
                var_srv_dependencies += f'        (t_eAPPACT_Actuators *)(&c_AppLgc_ActService{service_cfg[0]}Mapp_ae),\n'
                for idx_act, actuator in enumerate(service_cfg[1:]):
                    if str(actuator) != 'None':
                        if idx_act == 0:
                            enm_dependencies += f'        APPLGC_ACT_{str(actuator).upper()} = 0x00,\n'
                        else:
                            enm_dependencies += f'        APPLGC_ACT_{str(actuator).upper()},\n'

                        var_depencies += f'        {ENUM_APPACT_ACTUATOR_RT}_{str(actuator).upper()},\n'

                var_max_act_value += f'        (t_uint8)APPLGC_{str(service_cfg[0]).upper()}_ACT_NB,\n'
                var_depencies += '    };\n\n'
                enm_dependencies += f'        APPLGC_{str(service_cfg[0]).upper()}_ACT_NB,\n'
                enm_dependencies += '    } ' +f't_eAPPLGC_Srv{service_cfg[0]};\n\n'

                var_act_srv_asso += f'    g_srvFuncInfo_as[{APPLGC_ENUM_SRV}_{str(service_cfg[0]).upper()}].actVal_pau = (t_uAPPACT_SetValue *)(&g_ActContainer{service_cfg[0]}_au);\n'

                if f_is_uds_ope:
                    uds_lgc_data["LOGIC"]["SERVICE"][str(service_cfg[0]).upper()] = {
                            'id' : f'{idx_srv}',
                            'description' : f'{service_cfg[-1]}'
                    }

        var_max_act_value += '    };\n\n'
        var_srv_dependencies += '    };\n\n'
        enum_srv += f'\n        {APPLGC_ENUM_SRV}_NB,\n'
        enum_srv += '    } t_eAPPLGC_SrvList;\n'

        if f_is_uds_ope:
            with open(f_udscfg_path, "r", encoding="utf-8") as json_file:
                try:
                    existing_data = json.load(json_file)
                except json.JSONDecodeError:
                    existing_data = {}
            with open(f_udscfg_path, "w", encoding="utf-8") as json_file:
                existing_data.update(uds_lgc_data)
                json.dump(existing_data, json_file, indent=4, ensure_ascii=False)

        #-----------------------------------------------------------------
        #------------------------make drivers-----------------------------
        #-----------------------------------------------------------------
       
        #-----------------------------------------------------------------
        #------------------------make code gen----------------------------
        #-----------------------------------------------------------------
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("<<<<<<<<<<<<<<<<<<<<Start code generation for AppSdm Module>>>>>>>>>>>>>>>>>>>")
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("\t- For configPublic file")
        print("\t\t- enum agent/service")
        cls.code_gen.change_target_balise(TARGET_T_ENUM_START_LINE,TARGET_T_ENUM_END_LINE)
        cls.code_gen._write_into_file(enum_agent, APPLGC_CONFIGPUBLIC_PATH)
        cls.code_gen._write_into_file(enum_srv, APPLGC_CONFIGPUBLIC_PATH)
        cls.code_gen._write_into_file(enm_dependencies, APPLGC_CONFIGPUBLIC_PATH)

        
        print("\t- For configPrivate file")
        cls.code_gen.change_target_balise(TARGET_T_VARIABLE_START_LINE,TARGET_T_VARIABLE_END_LINE)
        cls.code_gen._write_into_file(var_srv_dependencies, APPLGC_CONFIGPRIVATE_PATH)
        cls.code_gen._write_into_file(var_depencies, APPLGC_CONFIGPRIVATE_PATH)
        cls.code_gen._write_into_file(var_max_act_value, APPLGC_CONFIGPRIVATE_PATH)
        cls.code_gen._write_into_file(var_agent, APPLGC_CONFIGPRIVATE_PATH)
    
        print("\tFor Logic.c")
        cls.code_gen.change_target_balise(TARGET_VARIABLE_START_LINE,TARGET_VARIABLE_END_LINE)
        cls.code_gen._write_into_file(decl_srv_val_container, APPLGC_C)
        cls.code_gen.change_target_balise(TARGET_ASSP_SRV_ACT_VALUE_START, TARGET_ASSP_SRV_ACT_VALUE_END)
        cls.code_gen._write_into_file(var_act_srv_asso, APPLGC_C)
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("<<<<<<<<<<<<<<<<<<<<End code generation for AppSdm Module>>>>>>>>>>>>>>>>>>>>>")
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n\n")
        
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

