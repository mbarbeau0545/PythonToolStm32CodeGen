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
from PyCodeGene import LoadConfig_FromExcel as LCFE, TARGET_T_END_LINE,TARGET_T_ENUM_END_LINE, \
                                                    TARGET_T_ENUM_START_LINE,TARGET_T_START_LINE,TARGET_T_VARIABLE_START_LINE,\
                                                    TARGET_T_VARIABLE_END_LINE,TARGET_T_STRUCT_START_LINE,\
                                                    TARGET_T_STRUCT_END_LINE
from typing import List, Dict
from PythonToolCfg.FMK_PATH import * 
#------------------------------------------------------------------------------
#                                       CONSTANT
#------------------------------------------------------------------------------
TARGET_SWITCH_CASE_HR_LINE_START = "            /* CAUTION : Automatic generated code section for switch case mapping: Start */\n"
TARGET_SWITCH_CASE_HR_LINE_STOP = "            /* CAUTION : Automatic generated code section for switch case mapping: Stop */\n"
TARGET_IRQHAND_HR_LINE_START = "    /* CAUTION : Automatic generated code section for IRQ Handler: Start */\n"
TARGET_IRQHAND_HR_LINE_STOP = "    /* CAUTION : Automatic generated code section for IRQ Handler: Stop */\n"
TARGET_VARIABLE_HR_LINE_START = "/* CAUTION : Automatic generated code section for Variables: Start */\n"
TARGET_VARIABLE_HR_LINE_STOP  = "/* CAUTION : Automatic generated code section for Variables: Stop */\n"

ENUM_ROOT_HR_LINE = "FMKHRT_HR_LINE"
ENUM_ROOT_HR_TIM = "FMKHRT_HIGH_RES_TIMER"
ENUM_ROOT_HR_SLV = "FMKHRT_HRTIM_SLAVE"
ENUM_ROOT_HR_CHNL = "FMKHRT_HRTIM_CHANNEL"
# CAUTION : Automatic generated code section: Start #

# CAUTION : Automatic generated code section: End #
LETTER_LIST = ["A", "B", "C", "D", "E", "F", "I", "J", "K"]

#------------------------------------------------------------------------------
#                                       CLASS
#------------------------------------------------------------------------------
class HighResTimerCfg_alreadyUsed(Exception):
    pass

class FMKHRT_CodeGen():
    """
            Make code generation for FMKTIM module which include 
            file FMKHRT_ConfigPublic.h : 
               - Enum Hr Line  x
            
            file FMKHRT_ConfigPrivate.h :
                - mapping ChnlLineMapp                       x

            file  FMKHRT.c
                - variable g_HrTimInfo_as init          x  
                - IRQN Handler
        """
    code_gen = LCFE()
    stm_tim_chnl = []
    #-------------------------
    # code_generation
    #-------------------------
    @classmethod
    def code_generation(cls, f_hw_cfg) -> None:

        cls.code_gen.load_excel_file(f_hw_cfg)
        timer_cfg_a     = cls.code_gen.get_array_from_excel("GI_HrtilInfo")
        list_irqn_hdler = cls.code_gen.get_array_from_excel('FMKHRT_IrqHandler')[1:]

       
        gencode_irqn_hdler = ""
        enum_hr_line = ""
        enum_channel = ""
        enum_slave = ""
        enum_highres_timer = ""
        const_mapp_chnl_line = ""
        switch_mapp_line = ""
        var_timcfg = ""
        
        desc_hr_line = []
        nb_slave = 0 
        nb_channel = 0 
        nb_hr_line = 0
       

        #----------------------------------------------------------------
        #-----------------------------make timer enum--------------------
        #-----------------------------------------------------------------

        const_mapp_chnl_line +=  "    /**< Interrupt Line/Channel Mapping for  High Resolution Line */\n" \
                                + "    const t_eFMKHRT_HighResLine c_FMkHrt_ChnlLineMapp_ae[FMKHRT_HIGH_RES_TIMER_NB][FMKHRT_HRTIM_SLAVE_NB][FMKHRT_HRTIM_CHANNEL_NB] = {\n"
        var_timcfg += "/**<  High Resolution Timer Cfg */\n" \
                    + "const t_sFMKHRT_HrTimerCfg c_FmkHrt_HrTimCfg_as[FMKHRT_HIGH_RES_TIMER_NB] = {\n"



        for idx, timer_cfg in enumerate(timer_cfg_a[1:]):
            try:
                if(int(timer_cfg[1]) > nb_slave):
                    nb_slave = int(timer_cfg[1])

                if(int(timer_cfg[2]) > nb_channel):
                    nb_channel = int(timer_cfg[2])

            except(TypeError):
                raise TypeError('Element of array must be a number')

            
            const_mapp_chnl_line += f'    [{ENUM_ROOT_HR_TIM}_{int(idx+1)}] = ' + '{\n'
            var_timcfg += f'    [{ENUM_ROOT_HR_TIM}_{int(idx+1)}] = ' + '{\n'\
                        + f'        .bspItsc_ps = {str(timer_cfg[0])},\n'\
                        + f'        .c_clkPort_e = {ENUM_FMKCPU_RCC_ROOT}_{str(timer_cfg[0])},\n'\
                        + f'        .c_MasterIRQNType_e = {ENUM_FMKCPU_NVIC_ROOT}_{timer_cfg[0]}_MASTER_IRQN,\n'

            var_timcfg += '            .c_SlaveTimIRQNType_ae = {\n'  
            for idx_slave in range(nb_slave):

                const_mapp_chnl_line += f'            [{ENUM_ROOT_HR_SLV}_{int(idx_slave + 1)}] = ' + '{\n'
                var_timcfg += f'                [{ENUM_ROOT_HR_SLV}_{int(idx_slave + 1)}] = {ENUM_FMKCPU_NVIC_ROOT}_{timer_cfg[0]}_TIM{LETTER_LIST[idx_slave]}_IRQN,\n'

                for idx_chnl in range(nb_channel):

                    nb_hr_line += 1 
                    const_mapp_chnl_line += f'                {ENUM_ROOT_HR_LINE}_{nb_hr_line},\n'

                    desc_hr_line.append(f"Reference to {timer_cfg[0]}, Timer Slave {LETTER_LIST[idx_slave]}, Channel {(idx_chnl + 1)}")

                    switch_mapp_line += f'            case {ENUM_ROOT_HR_LINE}_{nb_hr_line}:\n'\
                                    + '            {\n'\
                                    + '                if(f_HrTimIstc_pe != (t_eFMKHRT_HighResIstc *)NULL)\n'\
                                    + '                {\n'\
                                    + f'                    *f_HrTimIstc_pe = {ENUM_ROOT_HR_TIM}_{int(idx + 1)};\n'\
                                    + '                }\n'\
                                    + '                if(f_HrSlvTim_pe != (t_eFMKHRT_HighResSlvTim *)NULL)\n'\
                                    + '                {\n'\
                                    + f'                    *f_HrSlvTim_pe = {ENUM_ROOT_HR_SLV}_{int(idx_slave + 1)};\n'\
                                    + '                }\n'\
                                    + '                if(f_HrChnl_pe != (t_eFMKHRT_HrTimChannel  *)NULL)\n'\
                                    + '                {\n'\
                                    + f'                    *f_HrChnl_pe = {ENUM_ROOT_HR_CHNL}_{int(idx_chnl + 1)};'\
                                    + '                }\n'\
                                    + '                break;\n'\
                                    + '            }\n'
                                    
                const_mapp_chnl_line += '            },\n'
            var_timcfg += '            }\n'
            var_timcfg += '    },\n'
            const_mapp_chnl_line += '        },\n'


        var_timcfg += '};\n'
        const_mapp_chnl_line += '    };\n'
        enum_channel = cls.code_gen.make_enum_from_variable(ENUM_ROOT_HR_CHNL, [f"{int(idx_chnl + 1)}" for idx_chnl in range(nb_channel)],
                                                                't_eFMKHRT_HrTimChannel', 0, "High Resolution Timer Channel",
                                                                [f"Channel {int(idx_chnl + 1)}" for idx_chnl in range(nb_channel)])
        
        enum_slave = cls.code_gen.make_enum_from_variable(ENUM_ROOT_HR_SLV, [f"{int(idx_slave + 1)}" for idx_slave in range(nb_slave)],
                                                                't_eFMKHRT_HighResSlvTim', 0, "High Resolution Slave Timer Number",
                                                                [f"Timer Slave {LETTER_LIST[idx_slave]}" for idx_slave in range(nb_slave)])
        
        enum_highres_timer = cls.code_gen.make_enum_from_variable(  ENUM_ROOT_HR_TIM, [f"{str(timer_cfg[0])[-1]}" for timer_cfg in timer_cfg_a[1:]],
                                                                    't_eFMKHRT_HighResIstc', 0, "High Resolution Timer Instance Number",
                                                                    [f"Timer Resolution  {idx_high_res}" for idx_high_res in range(len(timer_cfg_a[1:]))])
        
        enum_hr_line = cls.code_gen.make_enum_from_variable(  ENUM_ROOT_HR_LINE, [f"{int(idx_hr_line + 1)}" for idx_hr_line in range(nb_hr_line)],
                                                                    't_eFMKHRT_HighResLine', 0, "High Resolution Line Avaiblable on CPU",
                                                                    desc_hr_line)
        #----------------------------------------------------------------
        #-------------------make IRQN HANDLER DECALRATION----------------
        #----------------------------------------------------------------
        for irqn_handler in list_irqn_hdler:
            idx_hres = str(irqn_handler)[7]
            gencode_irqn_hdler += f'    void {str(irqn_handler[0])}(void)\n'\
                                + '    {\n'
            if 'MASTER' in str(irqn_handler).upper():
                gencode_irqn_hdler += f'        HAL_HRTIM_IRQHandler(   FMKHRT_PRIVATE_GetHandleTypeDef({ENUM_ROOT_HR_TIM}_{str(idx_hres)}),\n'\
                                    + f'                                HRTIM_TIMERINDEX_MASTER);\n'
            else:           
                 gencode_irqn_hdler += f'        HAL_HRTIM_IRQHandler(   FMKHRT_PRIVATE_GetHandleTypeDef({ENUM_ROOT_HR_TIM}_{str(idx_hres)}),\n'\
                                    + f'                                HRTIM_TIMERINDEX_TIMER_{str(irqn_handler)[12]});\n'  
            gencode_irqn_hdler += '        return;\n'\
                                + '    }\n'

    

       


        #-----------------------------------------------------------
        #------------code genration for FMKTIM module---------------
        #-----------------------------------------------------------
        #---------------------For FMKTIM_Config Public---------------------#
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("<<<<<<<<<<<<<<<<<<<<Start code generation for FMFTIM Module>>>>>>>>>>>>>>>>>>>>")
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("\t- For configPublic file")
        cls.code_gen.change_target_balise(TARGET_T_ENUM_START_LINE,TARGET_T_ENUM_END_LINE)

        print('\t\t- enum for High Resolution Line')
        cls.code_gen._write_into_file(enum_hr_line, FMKHRT_CFG_PUBLIC_PATH)

       
        print("\t- For configPrivate file")
        #---------------------For FMKTIM_Config Private---------------------#
        cls.code_gen.change_target_balise(TARGET_T_ENUM_START_LINE,TARGET_T_ENUM_END_LINE)

        print("\t\t- enum for timer channel")
        cls.code_gen._write_into_file(enum_channel, FMKHRT_CFG_SPEC_H)

        print("\t\t- enum for timer slave ")
        cls.code_gen._write_into_file(enum_slave, FMKHRT_CFG_SPEC_H)

        print("\t\t- enum for timer instance ")
        cls.code_gen._write_into_file(enum_highres_timer, FMKHRT_CFG_SPEC_H)

        cls.code_gen.change_target_balise(TARGET_T_VARIABLE_START_LINE, TARGET_T_VARIABLE_END_LINE)
      
        print("\t\t- Variable for max channel per timer")
        cls.code_gen._write_into_file(const_mapp_chnl_line, FMKHRT_CFG_PRIVATE_PATH)
        cls.code_gen._write_into_file(var_timcfg, FMKHRT_CFG_PRIVATE_PATH)
    

       
        #---------------------For FMKTIM.c---------------------#
        print("\t- For FMKTIM.c file")
        
        print("\t\t- Timer Switch Case start")
        cls.code_gen.change_target_balise(TARGET_SWITCH_CASE_HR_LINE_START, TARGET_SWITCH_CASE_HR_LINE_STOP)
        cls.code_gen._write_into_file(switch_mapp_line, FMKHRT_CFG_SPEC)

        print("\t\t- IRQ Handler start")
        cls.code_gen.change_target_balise(TARGET_IRQHAND_HR_LINE_START, TARGET_IRQHAND_HR_LINE_STOP)
        cls.code_gen._write_into_file(gencode_irqn_hdler, FMKHRT_CFG_PRIVATE_PATH)

        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("<<<<<<<<<<<<<<<<<<<<End code generation for FMKTIM Module>>>>>>>>>>>>>>>>>>>")
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n\n")

    #-------------------------
    # get_tim_chnl_used
    #-------------------------
    @classmethod
    def get_tim_chnl_used(cls)->List:
        return cls.stm_tim_chnl
    
    #-------------------------
    # get_tim_chnl_used
    #-------------------------
    @classmethod
    def get_itline_from_timcnl(cls, enum_idx_timer:str, enum_channel:str)->str:
        pass
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

