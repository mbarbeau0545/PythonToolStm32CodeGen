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

import shutil
import json
from PythonToolCfg.APP_PATH import *
from PyCodeGene import LoadConfig_FromExcel as LCFE, TARGET_T_END_LINE,TARGET_T_ENUM_END_LINE, \
                                                    TARGET_T_ENUM_START_LINE,TARGET_T_START_LINE,TARGET_T_VARIABLE_START_LINE,\
                                                    TARGET_T_VARIABLE_END_LINE,TARGET_T_STRUCT_START_LINE,\
                                                    TARGET_T_STRUCT_END_LINE, TARGET_T_INCLUDE_END, TARGET_T_INCLUDE_START
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
    def code_generation(cls, f_software_cfg, f_udscfg_path , f_is_uds_ope = False) -> None:
        
        # Load needed excel arrays
        cls.code_gen.load_excel_file(f_software_cfg)
        act_interface_cfg_a = cls.code_gen.get_array_from_excel("AppAct_ActInterface")[1:]
        drivers_cfg_a = cls.code_gen.get_array_from_excel("AppAct_DriverList")[1:]
        # make python varaible 
        enum_act = ""
        enum_drv = ""
        include_act = ""
        var_act_if_state = ""
        var_drv_state = ""
        var_act_if = ""
        var_drv = ""
        var_unities = ""
        uds_act_data = {}
        uds_act_data["SENSORS"] = {}
        #-----------------------------------------------------------------
        #-----------------------------make all enum-----------------------
        #-----------------------------------------------------------------
        if str(act_interface_cfg_a[0][0]) is not None:
            enum_act = cls.code_gen.make_enum_from_variable(ENUM_APPACT_ACTUATOR_RT, [f"{act_cfg[0]}_{act_cfg[1]}" for act_cfg in act_interface_cfg_a],
                                                            "t_eAPPACT_ActInterface", 0, "Enum for Actuators list",
                                                            [f"Actuator Device {act_cfg[0]}, Interface {act_cfg[1]}, {act_cfg[-1]}"  for act_cfg in act_interface_cfg_a])
        else:
            enum_act = cls.code_gen.make_enum_from_variable(ENUM_APPACT_ACTUATOR_RT, [],
                                                            "t_eAPPACT_ActInterface", 0, "Enum for Actuators Interface list",
                                                            [])

        
        if str(drivers_cfg_a[0][0]) is not None:
            enum_drv = cls.code_gen.make_enum_from_variable(ENUM_APPACT_DRV_RT, [str(drv_cfg[0]).upper() for drv_cfg in drivers_cfg_a],
                                                        "t_eAPPACT_ActDriverList", 0, "Enum for Actuators drivers list",
                                                        [str(drv_cfg[-1])  for drv_cfg in drivers_cfg_a])
        else:
            enum_drv = cls.code_gen.make_enum_from_variable(ENUM_APPACT_DRV_RT, [],
                                                        "t_eAPPACT_ActDriverList", 0, "Enum for Actuators drivers list",
                                                        [])
        
        #-----------------------------------------------------------------
        #--------------------make var act/state/ include------------------
        #-----------------------------Make Header/Src fil-----------------
        #-----------------------------------------------------------------
        var_act_if += "    ///@brief Variable for System Actuators Interface Ope Mngmt Info\n" \
                    + f"    const t_sAPPACT_SysActCfg c_AppAct_SysAct_as[{ENUM_APPACT_ACTUATOR_RT}_NB] =" +" {\n"
        var_act_dvc = "    ///@brief Variable for system Actuators Device Ope Mngmt\n"\
                    + "    const t_sAPPACT_ActDvcOpeCfg c_AppAct_ActDvcOpeCfg_as[APPACT_ACTDVC_NB] = {\n"
        act_dvc_list = []
        for idx, act_cfg in enumerate(act_interface_cfg_a):
            # replace deebug signal with default if not use by user
            if act_cfg[2] == None or act_cfg[2] == 'None':
                act_cfg[2] = 'NB'
            if act_cfg[3] == None or act_cfg[3] == 'None':
                act_cfg[3] = 'NB'
            if act_cfg[4] == None or act_cfg[4] == 'None':
                act_cfg[4] = 'NB'

            if len(act_cfg[2]) > 32:
                raise ValueError(f'{act_cfg[2]} is to long to be open in PCAN Symbol get {len(act_cfg[2])} expect less than 32')
            if len(act_cfg[3]) > 32:
                raise ValueError(f'{act_cfg[3]} is to long to be open in PCAN Symbol get {len(act_cfg[3])} expect less than 32')
            if len(act_cfg[4]) > 32:
                raise ValueError(f'{act_cfg[4]} is to long to be open in PCAN Symbol,  get {len(act_cfg[4])} expect less than 32')
            
            if str(act_cfg[0]) is not None:
                # make var sensors
                var_act_if += "        {" \
                            + f"APPACT_ACTDVC_{act_cfg[0]},"\
                            + " " * ((SPACE_VARIABLE * 2) - len(f"APPACT_ACTDVC_{act_cfg[0]}")) \
                            + f"{VAR_APPACT_SPEC}_{act_cfg[0]}_{act_cfg[1]}_SetValue," \
                            + " " * ((SPACE_VARIABLE * 2) - len(f"{VAR_APPACT_SPEC}_{act_cfg[0]}_{act_cfg[1]}_SetValue,")) \
                            + f"{VAR_APPACT_SPEC}_{act_cfg[0]}_{act_cfg[1]}_GetValue,"\
                            + " " * ((SPACE_VARIABLE * 2) - len(f"{VAR_APPACT_SPEC}_{act_cfg[0]}_{act_cfg[1]}_GetValue,"))\
                            + f"APPSIG_SIGNAL_{act_cfg[2]},"\
                            + " " * ((SPACE_VARIABLE * 2) - len(f"APPSIG_SIGNAL_{act_cfg[2]}"))\
                            + f"APPSIG_SIGNAL_{act_cfg[3]},"\
                            + " " * ((SPACE_VARIABLE * 2) - len(f"APPSIG_SIGNAL_{act_cfg[3]}"))\
                            + f"APPSIG_SIGNAL_{act_cfg[4]}"\
                            + "},"\
                            + "//" + f"{ENUM_APPACT_ACTUATOR_RT}_{act_cfg[0]}_{act_cfg[1]}\n"
                              # make var unities
                # make include 
                include_act += f'    #include "{ACT_SPEC_FOLDER_PATH}/{VAR_APPACT_SPEC}_{act_cfg[0]}.h"\n'
                # make header/src file if needed
                if not os.path.isfile(f"{ACT_SPEC_FOLDER_FULLPATH}/{VAR_APPACT_SPEC}_{act_cfg[0]}.h"):
                    if act_cfg[0] not in act_dvc_list:
                        print(f"Couldn't find reference for {act_cfg[0]}")
                        cls.make_header_src_file(act_interface_cfg_a, str(act_cfg[0]))
                else:
                    print(f"Header/Source file for {act_cfg[0]} already existing")

                if act_cfg[0] not in act_dvc_list:
                    act_dvc_list.append(act_cfg[0])
                    var_act_dvc += '        {'\
                                + f'APPSYS_OPT_ID_ACT_{act_cfg[0]},'\
                                + " " * ((SPACE_VARIABLE * 2) - len(f"APPSYS_OPT_ID_ACT_{act_cfg[0]}"))\
                                + f'{VAR_APPACT_SPEC}_{act_cfg[0]}_SetCfg'\
                                + '},'\
                                + " " * ((SPACE_VARIABLE * 2) - len(f'{VAR_APPACT_SPEC}_{act_cfg[0]}_SetCfg'))\
                                + f' // APPACT_ACTDVC_{act_cfg[0]}\n'
                # uds cfg 
                if f_is_uds_ope:
                    uds_act_data["SENSORS"][str(act_cfg[0]).upper()] = {
                            'id' : f'{idx}',
                            'description' : f'{act_cfg[-1]}'
                    }

        var_act_dvc += '    };\n\n'
        var_act_if_state += "};\n\n"
        var_act_if += "    };\n\n"
        enm_dvc_list = cls.code_gen.make_enum_from_variable("APPACT_ACTDVC", act_dvc_list, "t_eAPPACT_ActDeviceList", 
                                                            0, "Enumeration of all sensors device list")

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
                    + "    const t_sAPPACT_SysDrvFunc c_AppAct_SysDrvCfg_as[APPACT_DRV_NB] = {\n"
        var_drv_state += "/**< Variable for Actuators Drivers State*/\n"
        var_drv_state += "t_eAPPACT_DrvState g_ActDrvState_ae[APPACT_DRV_NB] = {\n"
        for drv_cfg in drivers_cfg_a:
            if str(drv_cfg[0]) is not None:
                var_drv += "        {" 
                if "Yes" in str(drv_cfg[1]):
                    var_drv += f"(t_cbAppAct_DrvInit *){drv_cfg[0]}_Init,"
                    var_drv += " " * ((SPACE_VARIABLE * 2) - len(f"(t_cbAppAct_DrvInit *){VAR_DRV_ACT_FUNC_RT}_{drv_cfg[0]}_Init,"))
                else: 
                    var_drv += f"(t_cbAppAct_DrvInit *)NULL_FUNCTION,"
                    var_drv += " " * ((SPACE_VARIABLE * 2) - len(f"(t_cbAppAct_DrvInit *)NULL_FUNCTION,")) \
                
                if "Yes" in str(drv_cfg[2]):
                    var_drv += f"(t_cbAppAct_DrvCyclic *){drv_cfg[0]}_Cyclic,"
                    
                else: 
                    var_drv += f"(t_cbAppAct_DrvInit *)NULL_FUNCTION,"

                if 'Yes' in str(drv_cfg[3]):
                    var_drv += "TRUE}"
                    var_drv += " " * SPACE_VARIABLE
                else:
                    var_drv += "FALSE}"
                    var_drv += " " * SPACE_VARIABLE

                var_drv += f"  // {ENUM_APPACT_DRV_RT}_{str(drv_cfg[0]).upper()}\n"
                # make DRV state
        

        var_drv += "    };\n\n"
        #-----------------------------------------------------------------
        #------------------------make code gen----------------------------
        #-----------------------------------------------------------------
        print('[INFO] : APPACT_Codegen -> Config Public Code Generation')
        cls.code_gen.change_target_balise(TARGET_T_ENUM_START_LINE,TARGET_T_ENUM_END_LINE)
        cls.code_gen._write_into_file(enm_dvc_list, APPACT_CONFIGPUBLIC_PATH)
        cls.code_gen._write_into_file(enum_drv, APPACT_CONFIGPUBLIC_PATH)
        cls.code_gen._write_into_file(enum_act, APPACT_CONFIGPUBLIC_PATH)
        cls.code_gen.change_target_balise(TARGET_T_VARIABLE_START_LINE,TARGET_T_VARIABLE_END_LINE)
        
        print('[INFO] : APPACT_Codegen -> Config Private Code Generation')
        cls.code_gen._write_into_file(var_drv, APPACT_CONFIGPRIVATE_PATH)
        cls.code_gen._write_into_file(var_act_dvc, APPACT_CONFIGPRIVATE_PATH)
        cls.code_gen._write_into_file(var_act_if, APPACT_CONFIGPRIVATE_PATH)
        cls.code_gen.change_target_balise(TARGET_T_INCLUDE_START, TARGET_T_INCLUDE_END)
        cls.code_gen._write_into_file(include_act, APPACT_CONFIGPRIVATE_PATH)
    
    @classmethod
    def make_header_src_file(cls,f_actlist_cfg, f_act_name:str):
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
        suffix_func = {}
        suffix_func[f"SetCfg"] = ["(t_uint8 f_actDvcOpt_u8, t_eAPPACT_ActDriverList *f_drvUsed_pe)", "t_cbAppAct_SetActCfg"]
        for act_cfg in f_actlist_cfg:
            if act_cfg[0] == f_act_name:
                suffix_func[f"{act_cfg[1]}_GetValue"] = ["(t_float32 *f_rawSigValue_pf32)", "t_cbAppAct_GetIfValue" ]
                suffix_func[f"{act_cfg[1]}_SetValue"] = ["(t_float32 f_SigValue_pf32)", "t_cbAppAct_SetIfValue" ]

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

        print(f"[INFO] : APPACT_Codegen -> Succesfully create Header and Source file for {f_act_name}")


        


    
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

