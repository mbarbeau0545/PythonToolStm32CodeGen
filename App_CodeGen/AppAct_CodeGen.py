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
from PyCodeGene import LoadConfig_FromExcel as LCFE, TARGET_T_END_LINE,TARGET_T_ENUM_END_LINE, \
                                                    TARGET_T_ENUM_START_LINE,TARGET_T_START_LINE,TARGET_T_VARIABLE_START_LINE,\
                                                    TARGET_T_VARIABLE_END_LINE,TARGET_T_STRUCT_START_LINE,\
                                                    TARGET_T_STRUCT_END_LINE,TARGET_T_INCLUDE_START, TARGET_T_INCLUDE_END
#------------------------------------------------------------------------------
#                                       CONSTANT
#------------------------------------------------------------------------------


# CAUTION : Automatic generated code section: Start #

# CAUTION : Automatic generated code section: End #
#------------------------------------------------------------------------------
#                                       CLASS
#------------------------------------------------------------------------------
class AppAct_CodeGen():
    """
        Make code generation for FMKCDA module which include 
        file FMKCDA_ConfigPublic.h : 
            - Enum sensors                              
            - Enum drivers
            - Enum Sns Unities      
            - #include                    
        
        file FMKCDA_ConfigPrivate.h :
            - variable act config 
            - varaible drivers config
            - variable unity config

        file  APPACT.c
            - Default sensors state 
        create file 
            - APPACT_SPEC_sensors.c 
                template with "cfg/set/diag function"
            - APPACT_SPEC_sensors.h
                with declaration 
    """
    code_gen = LCFE()

    @classmethod
    def code_generation(cls, f_software_cfg, f_udscfg_path, f_is_uds_ope) -> None:
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("<<<<<<<<<<<<<<<<<<<<Start code generation for AppAct Module>>>>>>>>>>>>>>>>>>>")
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        # Load needed excel arrays
        cls.code_gen.load_excel_file(f_software_cfg)
        actuators_cfg_a = cls.code_gen.get_array_from_excel("AppAct_Actuators")[1:]
        drivers_cfg_a = cls.code_gen.get_array_from_excel("AppAct_Drivers")[1:]

        # make python varaible 
        enum_act = ""
        enum_drv = ""
        include_act = ""
        var_act_state = ""
        var_drv_state = ""
        var_act = ""
        var_drv = ""
        var_unities = ""
        uds_act_data = {}
        uds_act_data["ACTUATORS"] = {}
        #-----------------------------------------------------------------
        #-----------------------------make all enum-----------------------
        #-----------------------------------------------------------------
        if str(actuators_cfg_a[0][0]) != EMPTY_CELL:
            enum_act = cls.code_gen.make_enum_from_variable(ENUM_APPACT_ACTUATOR_RT, [str(act_cfg[0]).upper() for act_cfg in actuators_cfg_a],
                                                            "t_eAPPACT_Actuators", 0, "Enum for Actuators list",
                                                            [str(act_cfg[-1])  for act_cfg in actuators_cfg_a])
        else:
            enum_act = cls.code_gen.make_enum_from_variable(ENUM_APPACT_ACTUATOR_RT, [],
                                                            "t_eAPPACT_Actuators", 0, "Enum for Actuators list",
                                                            [])
            
        if str(drivers_cfg_a[0][0]) != EMPTY_CELL:
            enum_drv = cls.code_gen.make_enum_from_variable(ENUM_APPACT_DRV_RT, [str(drv_cfg[0]).upper() for drv_cfg in drivers_cfg_a],
                                                        "t_eAPPACT_Drivers", 0, "Enum for Actuators drivers list",
                                                        [str(drv_cfg[-1])  for drv_cfg in drivers_cfg_a])
        else:
            enum_drv = cls.code_gen.make_enum_from_variable(ENUM_APPACT_DRV_RT, [],
                                                        "t_eAPPACT_Drivers", 0, "Enum for Actuators drivers list",
                                                        [])
        
        #-----------------------------------------------------------------
        #--------------------make var act/state/ include------------------
        #-----------------------------Make Header/Src fil-----------------
        #-----------------------------------------------------------------
        var_act += "    /**< Variable for System Actuators functions*/\n" \
                    + "    const t_sAPPACT_SysActFunc c_AppAct_SysAct_apf[APPACT_ACTUATOR_NB] = {\n"
        var_act_state += "/**< Variable for Actuators Drivers State*/\n" \
                        + "t_eAPPACT_ActuatorState g_actState_ae[APPACT_ACTUATOR_NB] = {\n"
        for idx, act_cfg in enumerate(actuators_cfg_a):
            # make var sensors
            if(str(act_cfg[0]) != EMPTY_CELL):
                var_act += "        {" \
                            + f"{VAR_APPACT_SPEC}_{act_cfg[0]}_SetCfg," \
                            + " " * ((SPACE_VARIABLE * 2) - len(f"{VAR_APPACT_SPEC}_{act_cfg[0]}_SetCfg,")) \
                            + f"{VAR_APPACT_SPEC}_{act_cfg[0]}_SetValue," \
                            + " " * ((SPACE_VARIABLE * 2) - len(f"{VAR_APPACT_SPEC}_{act_cfg[0]}_SetValue,")) \
                            + f"{VAR_APPACT_SPEC}_{act_cfg[0]}_GetValue" \
                            + "}, //" + f"{ENUM_APPACT_ACTUATOR_RT}_{str(act_cfg[0]).upper()}\n"
                # make var state
                var_act_state += "    " \
                                + f"{ENUM_APPACT_ACTUATOR_ST_RT}_{str(act_cfg[1]).upper()}," \
                                + f" // {ENUM_APPACT_ACTUATOR_RT}_{str(act_cfg[0]).upper()}\n"
                # make include 
                include_act += f'    #include "{ACT_SPEC_FOLDER_PATH}/{VAR_APPACT_SPEC}_{act_cfg[0]}.h"\n'
                # make header/src file if needed
                if not os.path.isfile(f"{ACT_SPEC_FOLDER_FULLPATH}/{VAR_APPACT_SPEC}_{act_cfg[0]}.h"):
                    print(f"\t- Couldn't find reference for {act_cfg[0]}, Create Header/Source file")
                    cls.make_header_src_file(str(act_cfg[0]))
                else:
                    print(f"\t- Header/Source file for {act_cfg[0]} already existing, no operation")

                # uds cfg 
                if f_is_uds_ope:
                    uds_act_data["ACTUATORS"][str(act_cfg[0]).upper()] = {
                            'id' : f'{idx}',
                            'default_state' : f'{str(act_cfg[1]).upper()}',
                            'description' : f'{act_cfg[2]}'
                    }

        var_act_state += "};\n\n"
        var_act += "    };\n\n"

        if f_is_uds_ope:
            with open(f_udscfg_path, "r", encoding="utf-8") as json_file:
                try:
                    existing_data = json.load(json_file)
                except json.JSONDecodeError:
                    existing_data = {}
            with open(f_udscfg_path, "w", encoding="utf-8") as json_file:
                existing_data.update(uds_act_data)
                json.dump(existing_data, json_file, indent=4, ensure_ascii=False)


        #-----------------------------------------------------------------
        #------------------------make drivers-----------------------------
        #-----------------------------------------------------------------
        var_drv += "    /**< Variable for System Actuators drivers functions*/\n" \
                    + "    const t_sAPPACT_SysDrvFunc c_AppAct_SysDrv_apf[APPACT_DRIVER_NB] = {\n"
        var_drv_state += "/**< Variable for Actuators Drivers State*/\n"
        var_drv_state += "t_eAPPACT_DriverState g_ActDrvState_ae[APPACT_DRIVER_NB] = {\n"
        for drv_cfg in drivers_cfg_a:
            if(str(drv_cfg[0]) != EMPTY_CELL):
                var_drv += "        {" 
                if "Yes" in str(drv_cfg[1]):
                    var_drv += f"{drv_cfg[0]}_Init,"
                    var_drv += " " * ((SPACE_VARIABLE * 2) - len(f"{VAR_DRV_ACT_FUNC_RT}_{drv_cfg[0]}_Init"))
                else: 
                    var_drv += f"(t_cbAppAct_DrvInit *)NULL_FUNCTION,"
                    var_drv += " " * ((SPACE_VARIABLE * 2) - len(f"(t_cbAppAct_DrvInit *)NULL_FUNCTION,")) \
                
                if "Yes" in str(drv_cfg[2]):
                    var_drv += f"{drv_cfg[0]}_Cyclic" + "},"
                    
                else: 
                    var_drv += f"(t_cbAppAct_DrvInit *)NULL_FUNCTION" + "},"
        
                var_drv += f"  // {ENUM_APPACT_DRV_RT}_{str(drv_cfg[0]).upper()}\n"
                # make DRV state
                var_drv_state += f"        {ENUM_APPACT_DRVSTATE_RT}_{str(drv_cfg[3]).upper()}, // {ENUM_APPACT_DRV_RT}_{str(drv_cfg[0]).upper()}\n"
            
        var_drv_state += "};\n\n"
        var_drv += "    };\n\n"
        #-----------------------------------------------------------------
        #------------------------make code gen----------------------------
        #-----------------------------------------------------------------
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("<<<<<<<<<<<<<<<<<<<<Start code generation for AppAct Module>>>>>>>>>>>>>>>>>>>")
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("\t- For configPublic file")
        print("\t\t- Write enum act, drv, unity")
        cls.code_gen.change_target_balise(TARGET_T_ENUM_START_LINE,TARGET_T_ENUM_END_LINE)
        cls.code_gen._write_into_file(enum_drv, APPACT_CONFIGPUBLIC_PATH)
        cls.code_gen._write_into_file(enum_act, APPACT_CONFIGPUBLIC_PATH)
        cls.code_gen.change_target_balise(TARGET_T_VARIABLE_START_LINE,TARGET_T_VARIABLE_END_LINE)
        cls.code_gen._write_into_file(var_unities, APPACT_CONFIGPRIVATE_PATH)
        cls.code_gen._write_into_file(var_act, APPACT_CONFIGPRIVATE_PATH)
        cls.code_gen._write_into_file(var_drv, APPACT_CONFIGPRIVATE_PATH)
        cls.code_gen.change_target_balise(TARGET_T_INCLUDE_START, TARGET_T_INCLUDE_END)
        cls.code_gen._write_into_file(include_act, APPACT_CONFIGPRIVATE_PATH)
        print("\t- For configPrivate file")
        print("\t\t- Write variable act_cfg, drv_cfg")
        cls.code_gen.change_target_balise(TARGET_T_VARIABLE_START_LINE[4:],TARGET_T_VARIABLE_END_LINE[4:])

        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("<<<<<<<<<<<<<<<<<<<<End code generation for AppSns Module>>>>>>>>>>>>>>>>>>>>>")
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n\n")

    @classmethod
    def make_header_src_file(cls, f_act_name:str):
        """
            @brief Make .h and .c ACTSPEC file with funcction declaration 
        """
        var_func_impl = ""
        var_func_decl = ""
        func_name = ""
        ifdef_h =f"#ifndef {VAR_APPACT_SPEC}_{str(f_act_name).upper()}\n" \
                +f"#define {VAR_APPACT_SPEC}_{str(f_act_name).upper()}\n"
        include_h = '    #include "TypeCommon.h"\n' \
                   + '    #include "APP_CFG/ConfigFiles/APPACT_ConfigPublic.h"\n' 
        include_c = f'#include "./{VAR_APPACT_SPEC}_{f_act_name}.h"\n'
        suffix_func = {
            "SetCfg" : ["(void)", "t_cbAppAct_SetActCfg"], 
            "GetValue" :  ["(t_uAPPACT_GetValue *f_value_pu)", "t_cbAppAct_GetActValue" ],
            "SetValue" : ["(t_uAPPACT_SetValue f_value_u)", "t_cbAppAct_SetActValue"]
            }
        if not os.path.isdir(ACT_SPEC_FOLDER_FULLPATH):
            os.makedirs(ACT_SPEC_FOLDER_FULLPATH)
        distination_file_h = os.path.join(ACT_SPEC_FOLDER_FULLPATH, f"{VAR_APPACT_SPEC}_{f_act_name}.h")
        distination_file_c = os.path.join(ACT_SPEC_FOLDER_FULLPATH, f"{VAR_APPACT_SPEC}_{f_act_name}.c")
        # copy both files with new name
        shutil.copy(TPL_APP_SPC_PATH_H, distination_file_h)
        shutil.copy(TPL_APP_SPC_PATH_C, distination_file_c)
        for key, val in  suffix_func.items():
            func_name = f"{VAR_APPACT_SPEC}_{f_act_name}_{key}"
            var_func_impl += "\n\n/******************************************\n" \
                            + f"* {func_name}\n"  \
                            + "******************************************/\n" \
                            + f"t_eReturnCode {func_name}{val[0]}\n" \
                            + "{\n" + "    t_eReturnCode Ret_e = RC_OK;\n" \
                            + f"    //    Your code for {f_act_name}_{val[1][11:]} here\n\n\n\n" \
                            + "    return Ret_e;\n" + "}\n\n"
            var_func_decl += "    /**\n" \
                            + "    *\n" \
                            + f"    * @brief     @ref {val[1]}\n" \
                            + "    *\n" \
                            + "    */\n" \
                            + f"    t_eReturnCode {func_name}{val[0]};\n\n"
        # write down information declaration 
        cls.code_gen.change_target_balise(TARGET_FUNCTION_DECL_START, TARGET_FUNCTION_DECL_END)
        cls.code_gen._write_into_file(var_func_decl, distination_file_h)
        cls.code_gen.change_target_balise(TARGET_FUNCTION_IMP_START, TARGET_FUNCTION_IMP_END)
        cls.code_gen._write_into_file(var_func_impl, distination_file_c)
        cls.code_gen.change_target_balise(TARGET_T_INCLUDE_START, TARGET_T_INCLUDE_END)
        cls.code_gen._write_into_file(include_h, distination_file_h)
        cls.code_gen.change_target_balise(TARGET_T_INCLUDE_START[4:], TARGET_T_INCLUDE_END[4:])
        cls.code_gen._write_into_file(include_c, distination_file_c)
        cls.code_gen.change_target_balise(TARGET_FUNCTION_IFDEF_START,TARGET_FUNCTION_IFDEF_END)
        cls.code_gen._write_into_file(ifdef_h, distination_file_h)

        print(f"Succesfully create Header and Source file for {f_act_name}")
        
        
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

