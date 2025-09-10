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
class AppSns_CodeGen():
    """
        Make code generation for FMKCDA module which include 
        file FMKCDA_ConfigPublic.h : 
            - Enum sensors                              
            - Enum drivers
            - Enum Sns Unities      
            - #include                    
        
        file FMKCDA_ConfigPrivate.h :
            - variable sns config 
            - varaible drivers config
            - variable unity config

        file  APPSNS.c
            - Default sensors state 
        create file 
            - APPSNS_SPEC_sensors.c 
                template with "cfg/set/diag function"
            - APPSNS_SPEC_sensors.h
                with declaration 
    """
    code_gen = LCFE()

    @classmethod
    def code_generation(cls, f_software_cfg, f_udscfg_path , f_is_uds_ope = False) -> None:
        
        # Load needed excel arrays
        cls.code_gen.load_excel_file(f_software_cfg)
        sns_interface_cfg_a = cls.code_gen.get_array_from_excel("AppSns_SnsInterface")[1:]
        drivers_cfg_a = cls.code_gen.get_array_from_excel("AppSns_DriverList")[1:]
        unities_cfg_a = cls.code_gen.get_array_from_excel("AppSns_Unities")[1:]
        # make python varaible 
        enum_sns = ""
        enum_drv = ""
        enum_unity = ""
        include_sns = ""
        var_sns_if_state = ""

        var_sns_if = ""
        var_drv = ""
        var_unities = ""
        uds_sns_data = {}
        uds_sns_data["SENSORS"] = {}
        #-----------------------------------------------------------------
        #-----------------------------make all enum-----------------------
        #-----------------------------------------------------------------
        if str(sns_interface_cfg_a[0][0]) != EMPTY_CELL:
            enum_sns = cls.code_gen.make_enum_from_variable(ENUM_APPSNS_SNSS_RT, [f"{sns_cfg[0]}_{sns_cfg[1]}" for sns_cfg in sns_interface_cfg_a],
                                                            "t_eAPPSNS_SnsInterface", 0, "Enum for Sensors list",
                                                            [f"Sensors Device {sns_cfg[0]}, Interface {sns_cfg[1]}, {sns_cfg[-1]}"  for sns_cfg in sns_interface_cfg_a])
        else:
            enum_sns = cls.code_gen.make_enum_from_variable(ENUM_APPSNS_SNSS_RT, [],
                                                            "t_eAPPSNS_SnsInterface", 0, "Enum for Sensors Interface list",
                                                            [])

        
        if str(drivers_cfg_a[0][0]) != EMPTY_CELL:
            enum_drv = cls.code_gen.make_enum_from_variable(ENUM_APPSNS_DRV_RT, [str(drv_cfg[0]).upper() for drv_cfg in drivers_cfg_a],
                                                        "t_eAPPSNS_SnsDriverList", 0, "Enum for Sensors drivers list",
                                                        [str(drv_cfg[-1])  for drv_cfg in drivers_cfg_a])
        else:
            enum_drv = cls.code_gen.make_enum_from_variable(ENUM_APPSNS_DRV_RT, [],
                                                        "t_eAPPSNS_SnsDriverList", 0, "Enum for Sensors drivers list",
                                                        [])
        
        enum_unity = cls.code_gen.make_enum_from_variable(ENUM_APPSNS_UNITY_RT, [str(unity[0]).upper() for unity in unities_cfg_a],
                                                        "t_eAPPSNS_SnsMeasType", 0, "Enum for sensor conversion list",
                                                        [str(unity[-1])  for unity in unities_cfg_a])
        #-----------------------------------------------------------------
        #--------------------make var sns/state/ include------------------
        #-----------------------------Make Header/Src fil-----------------
        #-----------------------------------------------------------------
        var_sns_if += "    ///@brief Variable for System Sensors Interface Ope Mngmt Info\n" \
                    + f"    const t_sAPPSNS_SysSnsCfg c_AppSns_SysSns_as[{ENUM_APPSNS_SNSS_RT}_NB] =" +" {\n"
        var_sns_dvc = "    ///@brief Variable for system Sensors Device Ope Mngmt\n"\
                    + "    const t_sAPPSNS_SnsDvcOpeCfg c_AppSns_SnsDvcOpeCfg_as[APPSNS_SNSDVC_NB] = {\n"
        sns_dvc_list = []
        for idx, sns_cfg in enumerate(sns_interface_cfg_a):
            if sns_cfg[3] == None or sns_cfg[3] == 'None':
                sns_cfg[3] = 'NB'
            if str(sns_cfg[0]) != EMPTY_CELL:
                # make var sensors
                var_sns_if += "        {" \
                            + f"APPSNS_SNSDVC_{sns_cfg[0]},"\
                            + " " * ((SPACE_VARIABLE * 2) - len(f"APPSNS_SNSDVC_{sns_cfg[0]}")) \
                            + f"{ENUM_APPSNS_UNITY_RT}_{sns_cfg[2]}," \
                            + " " * ((SPACE_VARIABLE * 2) - len(f"{ENUM_APPSNS_UNITY_RT}_{str(sns_cfg[2])}")) \
                            + f"{VAR_APPSNS_SPEC}_{sns_cfg[0]}_{sns_cfg[1]}_GetSigValue," \
                            + " " * ((SPACE_VARIABLE * 2) - len(f"{VAR_APPSNS_SPEC}_{sns_cfg[0]}_{sns_cfg[1]}_GetValue,")) \
                            + f"{VAR_APPSNS_SPEC}_{sns_cfg[0]}_{sns_cfg[1]}_FormatValue," \
                            + " " * ((SPACE_VARIABLE * 2) - len(f"{VAR_APPSNS_SPEC}_{sns_cfg[0]}_{sns_cfg[1]}_FormatValue,"))\
                            + f"APPSIG_SIGNAL_{sns_cfg[3]}"\
                            + "},"\
                            + "//" + f"{ENUM_APPSNS_SNSS_RT}_{sns_cfg[0]}_{sns_cfg[1]}\n"
                              # make var unities
                # make include 
                include_sns += f'    #include "{SNS_SPEC_FOLDER_PATH}/{VAR_APPSNS_SPEC}_{sns_cfg[0]}.h"\n'
                # make header/src file if needed
                if not os.path.isfile(f"{SNS_SPEC_FOLDER_FULLPATH}/{VAR_APPSNS_SPEC}_{sns_cfg[0]}.h"):
                    if sns_cfg[0] not in sns_dvc_list:
                        print(f"Couldn't find reference for {sns_cfg[0]}")
                        cls.make_header_src_file(sns_interface_cfg_a, str(sns_cfg[0]))
                else:
                    print(f"Header/Source file for {sns_cfg[0]} already existing")

                if sns_cfg[0] not in sns_dvc_list:
                    sns_dvc_list.append(sns_cfg[0])
                    var_sns_dvc += '        {'\
                                + f'APPSYS_OPT_ID_SNS_{sns_cfg[0]},'\
                                + " " * ((SPACE_VARIABLE * 2) - len(f"APPSYS_OPT_ID_SNS_{sns_cfg[0]}"))\
                                + f'{VAR_APPSNS_SPEC}_{sns_cfg[0]}_SetCfg'\
                                + '},'\
                                + " " * ((SPACE_VARIABLE * 2) - len(f'{VAR_APPSNS_SPEC}_{sns_cfg[0]}_SetCfg'))\
                                + f' // APPSNS_SNSDVC_{sns_cfg[0]}\n'
                # uds cfg 
                if f_is_uds_ope:
                    uds_sns_data["SENSORS"][str(sns_cfg[0]).upper()] = {
                            'id' : f'{idx}',
                            'Unity' : f'{str(sns_cfg[1]).upper()}',
                            'default_state' : f'{str(sns_cfg[2]).upper()}',
                            'description' : f'{sns_cfg[3]}'
                    }

        var_sns_dvc += '    };\n\n'
        var_sns_if_state += "};\n\n"
        var_sns_if += "    };\n\n"
        enm_dvc_list = cls.code_gen.make_enum_from_variable("APPSNS_SNSDVC", sns_dvc_list, "t_eAPPSNS_SnsDeviceList", 
                                                            0, "Enumeration of all sensors device list")

        if f_is_uds_ope:
            with open(f_udscfg_path, "r", encoding="utf-8") as json_file:
                try:
                    existing_data = json.load(json_file)
                except json.JSONDecodeError:
                    existing_data = {}
            with open(f_udscfg_path, "w", encoding="utf-8") as json_file:
                existing_data.update(uds_sns_data)
                json.dump(existing_data, json_file, indent=4, ensure_ascii=False)

        #-----------------------------------------------------------------
        #------------------------make drivers-----------------------------
        #-----------------------------------------------------------------
        var_drv += "    /**< Variable for System Sensors drivers functions*/\n" \
                    + "    const t_sAPPSNS_SysDrvFunc c_AppSns_SysDrv_as[APPSNS_DRV_NB] = {\n"
        for drv_cfg in drivers_cfg_a:
            if str(drv_cfg[0]) != EMPTY_CELL:
                var_drv += "        {" 
                if "Yes" in str(drv_cfg[1]):
                    var_drv += f"(t_cbAppSns_DrvInit *){drv_cfg[0]}_Init,"
                    var_drv += " " * ((SPACE_VARIABLE * 2) - len(f"(t_cbAppSns_DrvInit *){VAR_DRV_SNS_FUNC_RT}_{drv_cfg[0]}_Init,"))
                else: 
                    var_drv += f"(t_cbAppSns_DrvInit *)NULL_FUNCTION,"
                    var_drv += " " * ((SPACE_VARIABLE * 2) - len(f"(t_cbAppSns_DrvInit *)NULL_FUNCTION,")) \
                
                if "Yes" in str(drv_cfg[2]):
                    var_drv += f"(t_cbAppSns_DrvCyclic *){drv_cfg[0]}_Cyclic,"
                    
                else: 
                    var_drv += f"(t_cbAppSns_DrvInit *)NULL_FUNCTION,"

                if 'Yes' in str(drv_cfg[3]):
                    var_drv += "TRUE}"
                    var_drv += " " * SPACE_VARIABLE
                else:
                    var_drv += "FALSE}"
                    var_drv += " " * SPACE_VARIABLE

                var_drv += f"  // {ENUM_APPSNS_DRV_RT}_{str(drv_cfg[0]).upper()}\n"
                # make DRV state
        

        var_drv += "    };\n\n"
        #-----------------------------------------------------------------
        #------------------------make code gen----------------------------
        #-----------------------------------------------------------------
        print('[INFO] : APPSNS_Codegen -> Config Public Code Generation')
        cls.code_gen.change_target_balise(TARGET_T_ENUM_START_LINE,TARGET_T_ENUM_END_LINE)
        cls.code_gen._write_into_file(enum_unity, APPSNS_CONFIGPUBLIC_PATH)
        cls.code_gen._write_into_file(enm_dvc_list, APPSNS_CONFIGPUBLIC_PATH)
        cls.code_gen._write_into_file(enum_drv, APPSNS_CONFIGPUBLIC_PATH)
        cls.code_gen._write_into_file(enum_sns, APPSNS_CONFIGPUBLIC_PATH)
        cls.code_gen.change_target_balise(TARGET_T_VARIABLE_START_LINE,TARGET_T_VARIABLE_END_LINE)
        
        print('[INFO] : APPSNS_Codegen -> Config Private Code Generation')
        cls.code_gen._write_into_file(var_drv, APPSNS_CONFIGPRIVATE_PATH)
        cls.code_gen._write_into_file(var_sns_dvc, APPSNS_CONFIGPRIVATE_PATH)
        cls.code_gen._write_into_file(var_sns_if, APPSNS_CONFIGPRIVATE_PATH)
        cls.code_gen.change_target_balise(TARGET_T_INCLUDE_START, TARGET_T_INCLUDE_END)
        cls.code_gen._write_into_file(include_sns, APPSNS_CONFIGPRIVATE_PATH)
    
    @classmethod
    def make_header_src_file(cls,f_snslist_cfg, f_sns_name:str):
        """
            @brief Make .h and .c SNSSPEC file with funcction declaration 
        """
        var_func_impl = ""
        var_func_decl = ""
        func_name = ""
        ifdef_h =f"#ifndef {VAR_APPSNS_SPEC}_{str(f_sns_name).upper()}\n" \
                +f"#define {VAR_APPSNS_SPEC}_{str(f_sns_name).upper()}\n"
        include_h = '    #include "TypeCommon.h"\n' \
                   + '    #include "APP_CFG/ConfigFiles/APPSNS_ConfigPublic.h"\n' 
        include_c = f'#include "./{VAR_APPSNS_SPEC}_{f_sns_name}.h"\n'
        suffix_func = {}
        suffix_func[f"SetCfg"] = ["(t_uint8 f_snsDvcOpt_u8, t_eAPPSNS_SnsDriverList *f_drvUsed_pe)", "t_cbAppSns_SetSnsCfg"]
        for sns_cfg in f_snslist_cfg:
            if sns_cfg[0] == f_sns_name:
                suffix_func[f"{sns_cfg[1]}_GetSigValue"] = ["(t_float32 *f_rawSigValue_pf32, t_bool * f_isValue_OK)", "t_cbAppSns_GetSigValue" ]
                suffix_func[f"{sns_cfg[1]}_FormatValue"] = ["(t_float32  rawValue_f32, t_float32 *SnsValue_f32)", "t_cbAppSns_FormatValSI" ]

        if not os.path.isdir(SNS_SPEC_FOLDER_FULLPATH):
            os.makedirs(SNS_SPEC_FOLDER_FULLPATH)

        distination_file_h = os.path.join(SNS_SPEC_FOLDER_FULLPATH, f"{VAR_APPSNS_SPEC}_{f_sns_name}.h")
        distination_file_c = os.path.join(SNS_SPEC_FOLDER_FULLPATH, f"{VAR_APPSNS_SPEC}_{f_sns_name}.c")
        # copy both files with new name
        shutil.copy(TPL_APP_SPC_PATH_H, distination_file_h)
        shutil.copy(TPL_APP_SPC_PATH_C, distination_file_c)
        for key, val in  suffix_func.items():
            func_name = f"{VAR_APPSNS_SPEC}_{f_sns_name}_{key}"
            var_func_impl += "\n\n/******************************************\n" \
                            + f"* {func_name}\n"  \
                            + "******************************************/\n" \
                            + f"t_eReturnCode {func_name}{val[0]}\n" \
                            + "{\n" + "    t_eReturnCode Ret_e = RC_OK;\n" \
                            + f"    //    Your code for {f_sns_name}_{val[1][11:]} here\n\n\n\n" \
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

        print(f"[INFO] : APPSNS_Codegen -> Succesfully create Header and Source file for {f_sns_name}")


        


    
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

