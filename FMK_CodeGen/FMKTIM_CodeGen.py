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
TARGET_TIMER_INFO_START = "/* CAUTION : Automatic generated code section for Timer Configuration: Start */\n"
TARGET_TIMER_INFO_END   = "/* CAUTION : Automatic generated code section for Timer Configuration: End */\n"
TARGET_TIMER_CHNLNB_START = "    /* CAUTION : Automatic generated code section for Timer channels number: Start */\n"
TARGET_TIMER_CHNLNB_END   = "    /* CAUTION : Automatic generated code section for Timer channels number: End */\n"
TARGET_TIMER_X_IRQH_START = "/* CAUTION : Automatic generated code section for TIMx IRQHandler: Start */\n"
TARGET_TIMER_X_IRQH_END = "/* CAUTION : Automatic generated code section for TIMx IRQHandler: End */\n"

# CAUTION : Automatic generated code section: Start #

# CAUTION : Automatic generated code section: End #
#------------------------------------------------------------------------------
#                                       CLASS
#------------------------------------------------------------------------------
class TimerCfg_alreadyUsed(Exception):
    pass

class PeriphClockCfgError(Exception):
    pass

class FMKTIM_CodeGen():
    """
            Make code generation for FMKTIM module which include 
            file FMKTIM_ConfigPublic.h : 
               - Enum nUmber max of channel timer  x
               - Enum timer list                   x
               - Enum Event channel                x
            
            file FMKTIM_ConfigPrivate.h :
                - Variable Event timer cfg         x
            
            file  FMK_CPU_ConfigSpecififc.c
                - enable/ disable clock implementation  x

            file  FMK_CPU_ConfigSpecififc.h
                - -enable/ disable clock declaration    x

            file  FMK_CPU.c
                - variable g_timerInfo_as init          x  
                - switch case IRQN to bsp IRQN          x
                - hardware IRQNHandler for timer        
        """
    itline_timchnl_mapping:Dict[str, List[str]] = {}
    code_gen = LCFE()
    stm_tim_chnl = []
    #-------------------------
    # code_generation
    #-------------------------
    @classmethod
    def code_generation(cls, f_hw_cfg) -> None:

        cls.code_gen.load_excel_file(f_hw_cfg)
        timer_cfg_a     = cls.code_gen.get_array_from_excel("GI_Timer")

       

        enum_channel = ""
        enum_timer = ""
        enum_evnt = ""
        var_timcfg = ""
        const_mapp_chnl_itline = ""
        const_mapp_evnt_tim = ""
        const_mapp_gp_tim = ""
        const_mapp_dac_tim = ""
        const_tim_clk_src = ""
        enum_it_lines_gp = ""
        enum_it_lines_dac = ""
        enum_it_lines_evnt = ""
        func_imple = ""
        def_tim_max_chnl = ""
        var_tim_max_chnl = ""
        max_channel: int = 0
        nb_evnt_channel = 0
        timer_number_a = []
        
       

        #----------------------------------------------------------------
        #-----------------------------make timer enum--------------------
        #-----------------------------------------------------------------
        suffix_dac_tim = []
        suffix_evnt_tim = []
        idx_tim_pg = 1
        idx_tim_evnt = 1
        idx_dac_tim = 1
        description_pg_tim   = []
        description_dac_tim  = []
        description_evnt_tim = []
        suffix_pg_tim = []
        const_mapp_chnl_itline +=  "    /**< Interrupt Line/Channel Mapping for IO IT Line */\n" \
                                + "    const t_sFMKTIM_ChnlITLineMapping c_FmkTim_ChnlItLineMapp[FMKTIM_TIMER_NB][FMKTIM_CHANNEL_NB] = {\n"
        var_timcfg += "/**< timer configuration variable */\n" \
                    + "    t_sFMKTIM_TimerCfg c_FmkTim_TimersCfg_as[FMKTIM_TIMER_NB] = {\n"
        var_tim_max_chnl += "    /**< timer max channel variable */\n" \
                            + "    const t_uint8 c_FMKTIM_TimMaxChnl_ua8[FMKTIM_TIMER_NB] = {\n"
        
        const_mapp_gp_tim += "    /**< General Purpose Timer Channel Mapping */\n" \
                            + f"    t_sFMKTIM_BspTimerCfg c_FmkTim_ITLineIOMapp_as[{ENUM_FMKTIM_IT_GP_ROOT}_NB] = " \
                            + "{\n"
        const_mapp_evnt_tim += "    /**< Event Purpose Timer Channel Mapping */\n" \
                            + f"    t_sFMKTIM_BspTimerCfg c_FmkTim_ITLineEvntMapp_as[{ENUM_FMKTIM_IT_EVNT_ROOT}_NB] = " \
                            + "{\n"
        const_mapp_dac_tim += "    /**< Dac Purpose Timer Channel Mapping */\n" \
                            + f"    t_sFMKTIM_BspTimerCfg c_FmkTim_ITLineDacMapp_as[{ENUM_FMKTIM_IT_DAC_ROOT}_NB] = " \
                            + "{\n"
        
        const_tim_clk_src += '    /**< Timer/Oscillator source constant */\n' \
                        +   f"    const t_eFMKTIM_SysClkOsc c_FmkTim_TimClkSrc_ae[FMKTIM_TIMER_NB] =" + '{\n'

        # found max channel first, needed after 
        for timer_cfg in timer_cfg_a[1:]:
            if (timer_cfg[1] > max_channel):
                max_channel = timer_cfg[1]

        for idx, timer_cfg in enumerate(timer_cfg_a[1:]):
            idx_timer = str(timer_cfg[0][3:])
            timer_number_a.append(idx_timer)

            var_timcfg += f'        [{ENUM_FMKTIM_TIMER_ROOT}_{idx_timer}] = ' + '{\n'\
                        + f"        .bspIstc_ps = TIM{idx_timer},\n" \
                        + f"        .c_clock_e = {ENUM_FMKCPU_RCC_ROOT}_TIM{idx_timer},\n" \
                        + f"        .c_IRQNType_e = {ENUM_FMKCPU_NVIC_ROOT}_{str(timer_cfg[2]).upper()}\n" \
                        + "    },\n"
            
            # make defines timer channel
            def_tim_max_chnl += f"    #define FMKTIM_MAX_CHNL_TIMER_{idx_timer} ((t_uint8){timer_cfg[1]})\n"

            # make varialble max timer channel 
            var_tim_max_chnl += f"        (t_uint8)FMKTIM_MAX_CHNL_TIMER_{idx_timer}," \
                                + " " * (SPACE_VARIABLE - len(f"FMKTIM_MAX_CHNL_TIMER_{idx_timer},")) \
                                + f"// {ENUM_FMKTIM_TIMER_ROOT}_{idx_timer}\n"  
                
            # make const var for tim clock source 
            const_tim_clk_src += f'        {ENUM_FKCPU_SYS_CLK}_{timer_cfg[4]},' \
                            + " " * (SPACE_VARIABLE - len(f"{ENUM_FKCPU_SYS_CLK}_{timer_cfg[4]}")) \
                            + f' // {ENUM_FMKTIM_TIMER_ROOT}_{idx_timer}\n'
            const_mapp_chnl_itline += f'        [{ENUM_FMKTIM_TIMER_ROOT}_{idx_timer}] = ' + '{\n'
            # make timer public enum
            channel = 0 
            if idx_timer == '6':
                print('[WARNING] Timer 6 detected, use to generate SysTick, this timer will not be used...')
            else:
                match  str(timer_cfg[3]).upper():
                    case 'PWM/IC/OC/OP':
                        
                        suffix_pg_tim.extend([f"{idx_tim_pg}{i}" for i in range(1, (timer_cfg[1] +1))])
                        description_pg_tim.extend(f"General Purpose Timer, Reference to Timer {idx_timer} Channel {channel}" for channel in range(1, (timer_cfg[1] +1)))
                        
                        for channel in range(1, (timer_cfg[1] +1)):
                            const_mapp_gp_tim += "        {" + f"{ENUM_FMKTIM_TIMER_ROOT}_{idx_timer},"  \
                                            + " " * (SPACE_VARIABLE - len(f"{ENUM_FMKTIM_TIMER_ROOT}_{idx_timer}")) \
                                            + f"        {ENUM_FMKTIM_CHANNEL_ROOT}_{channel}" \
                                            + "}," + f"    // {ENUM_FMKTIM_IT_GP_ROOT}_{idx_tim_pg}{channel}\n"
                            
                            const_mapp_chnl_itline += '            {'  + f'{ENUM_FMKTIM_IT_TYPE_ROOT}_IO,'\
                                                    + ' ' * (50 - len(f"{ENUM_FMKTIM_IT_TYPE_ROOT}_IO")) \
                                                    + f'{ENUM_FMKTIM_IT_GP_ROOT}_{idx_tim_pg}{channel}' + '},'  + f"    // {ENUM_FMKTIM_IT_GP_ROOT}_{idx_tim_pg}{channel}\n"

                            # for fmkio
                            cls.itline_timchnl_mapping[str(f"{ENUM_FMKTIM_TIMER_ROOT}_{idx_timer}{ENUM_FMKTIM_CHANNEL_ROOT}_{channel}")] =  f"{ENUM_FMKTIM_IT_GP_ROOT}_{idx_tim_pg}{channel}"
                        # update idx   
                        idx_tim_pg +=1
                        
                    case 'DAC':
                        suffix_dac_tim.extend(f"{int(idx_dac_tim + i)}" for i in range(0, (timer_cfg[1])))
                        description_dac_tim.extend(f"Dac Purpose Timer, Reference to Timer {idx_timer} Channel {channel}" for channel in range(1, (timer_cfg[1] +1)))

                        for channel in range(1, (timer_cfg[1] +1)):
                            const_mapp_dac_tim += "        {" + f"{ENUM_FMKTIM_TIMER_ROOT}_{idx_timer},"  \
                                                + " " * (SPACE_VARIABLE - len(f"{ENUM_FMKTIM_TIMER_ROOT}_{idx_timer},")) \
                                                + f"        {ENUM_FMKTIM_CHANNEL_ROOT}_{channel}" \
                                                + "}," + f"    // {ENUM_FMKTIM_IT_DAC_ROOT}_{idx_dac_tim}\n"
                            # for fmkio
                            cls.itline_timchnl_mapping[str(f"{ENUM_FMKTIM_TIMER_ROOT}_{idx_timer}{ENUM_FMKTIM_CHANNEL_ROOT}_{channel}")] =  f"{ENUM_FMKTIM_IT_DAC_ROOT}_{idx_dac_tim}"

                            const_mapp_chnl_itline += '            {'  + f'{ENUM_FMKTIM_IT_TYPE_ROOT}_DAC,'\
                                                    + ' ' * (50 - len(f"{ENUM_FMKTIM_IT_TYPE_ROOT}_DAC,")) \
                                                    + f'{ENUM_FMKTIM_IT_DAC_ROOT}_{idx_dac_tim}' + '},' + f"    // {ENUM_FMKTIM_IT_DAC_ROOT}_{idx_dac_tim}\n"
                        idx_dac_tim = idx_dac_tim + timer_cfg[1]

                    case 'EVENT':
                        channel += 1
                        nb_evnt_channel +=1
                        suffix_evnt_tim.append(f"{nb_evnt_channel}")
                        description_evnt_tim.append(f" Reference to timer {idx_timer}, CHANNEL_1")
                        const_mapp_evnt_tim += "        {" + f"{ENUM_FMKTIM_TIMER_ROOT}_{idx_timer},"  \
                                            + " " * (SPACE_VARIABLE - len(f"{ENUM_FMKTIM_TIMER_ROOT}_{idx_timer},")) \
                                            + f"        {ENUM_FMKTIM_CHANNEL_ROOT}_1"\
                                            + "}," + f"    // {ENUM_FMKTIM_IT_EVNT_ROOT}_1\n"

                        const_mapp_chnl_itline +=  '            {'  + f'{ENUM_FMKTIM_IT_TYPE_ROOT}_EVNT,'\
                                                + ' ' * (50 - len(f'{ENUM_FMKTIM_IT_TYPE_ROOT}_EVNT,')) \
                                                + f'{ENUM_FMKTIM_IT_EVNT_ROOT}_{nb_evnt_channel}' + '},' + f"    // {ENUM_FMKTIM_IT_EVNT_ROOT}_{nb_evnt_channel}\n"
                            
                        # for fmkio
                        cls.itline_timchnl_mapping[str(f"{ENUM_FMKTIM_TIMER_ROOT}_{idx_timer}{ENUM_FMKTIM_CHANNEL_ROOT}_{channel}")] =  f"{ENUM_FMKTIM_IT_EVNT_ROOT}_{idx_tim_evnt}"

                        idx_tim_evnt = idx_tim_evnt + timer_cfg[1]

            # complete mapp_chnl_itline with default value if the timer has x channels, x < max_channel
            for ___ in range(max_channel - channel):
                 const_mapp_chnl_itline +=  '            {'  + f'{ENUM_FMKTIM_IT_TYPE_ROOT}_NB,'\
                                                + ' ' * (50 - len(f"{ENUM_FMKTIM_IT_TYPE_ROOT}_NB")) \
                                                + f'FMKTIM_INTERRUPT_LINE_UNUSED' + '},' + f"    // NOT AVAILABLE ON HARDWARE\n"
                    
            const_mapp_chnl_itline += '        },\n'
            
        const_tim_clk_src += '    };\n\n'
        var_tim_max_chnl += "    };\n\n"
        var_timcfg += "};\n\n"
        const_mapp_gp_tim += "    };\n\n"
        const_mapp_evnt_tim += "    };\n\n"
        const_mapp_dac_tim += "    };\n\n"
        const_mapp_chnl_itline += '    };\n\n'

        enum_channel += "    /**< Number max of channel enable by timer */\n" \
                        + '     typedef enum\n    {\n'
        for idx in range(max_channel):
            if idx == 0:
                enum_channel += f'        {ENUM_FMKTIM_CHANNEL_ROOT}_{idx+1} = 0x00,' \
                            + ' ' * (SPACE_VARIABLE - len(f'{ENUM_FMKTIM_CHANNEL_ROOT}_{idx+1}')) \
                            + f'// Reference to HAL channel {idx + 1}\n'
            else:
                enum_channel += f'        {ENUM_FMKTIM_CHANNEL_ROOT}_{idx+1},' \
                            + ' ' * (SPACE_VARIABLE - len(f'{ENUM_FMKTIM_CHANNEL_ROOT}_{idx+1}')) \
                            + f'// f"Reference to HAL channel {idx + 1}\n'
            
        enum_channel += f'\n        {ENUM_FMKTIM_CHANNEL_ROOT}_NB,\n' \
                        + f'        {ENUM_FMKTIM_CHANNEL_ROOT}_ALL,\n' \
                        + '    } t_eFMKTIM_InterruptChnl;\n\n'
        #----------------------------------------------------------------
        #-------------------make IRQN HANDLER DECALRATION----------------
        #----------------------------------------------------------------
        irnq_list_treated = []
        for timer_info in timer_cfg_a[1:]:
            irqn_handler = timer_info[2]

            if irqn_handler in irnq_list_treated:
                continue

            timer = timer_info[0]
            # found the timer number
            idx_nb_tim = int(str(timer).index('M')+ 1)

            codgen_irqn_handler_call = f"        HAL_TIM_IRQHandler(FMKTIM_PRIVATE_GetHandleTypeDef((t_uint8){ENUM_FMKTIM_TIMER_ROOT}_{str(timer)[idx_nb_tim:]}));\n"
            # check if other timer use this irqn_handler 
            for other_tim_info in timer_cfg_a[1:]:
                if timer_info[0] != other_tim_info[0]:
                    if other_tim_info[2] == irqn_handler:
                        other_idx_tim = int(str(other_tim_info[0]).index('M')+ 1)
                        codgen_irqn_handler_call += f"        HAL_TIM_IRQHandler(FMKTIM_PRIVATE_GetHandleTypeDef((t_uint8){ENUM_FMKTIM_TIMER_ROOT}_{str(other_tim_info[0])[other_idx_tim:]}));\n"

            
            func_imple += '    /*********************************\n' \
                        + f'    * {irqn_handler[:-4]}IRQHandler\n' \
                        + '    *********************************/\n' \
                        + f'   void {irqn_handler[:-4]}IRQHandler(void)\n'\
                        + "    {\n"\
                        +f"{codgen_irqn_handler_call}"\
                        + '        return;\n'\
                        + "    }\n"
            
            irnq_list_treated.append(irqn_handler)
        #----------------------------------------------------------------
        #-----------------------------make var evnt cfg------------------
        #-----------------------------make eenum evnt channel------------
        #----------------------------------------------------------------
        enum_it_lines_gp = cls.code_gen.make_enum_from_variable(ENUM_FMKTIM_IT_GP_ROOT, suffix_pg_tim,
                                                                't_eFMKTIM_InterruptLineIO', 0, "Number of General Purpose Interrupt Line, for PWM, Input-Compare, Output Compare, One sPulse",
                                                                description_pg_tim)
        
        enum_it_lines_evnt = cls.code_gen.make_enum_from_variable(ENUM_FMKTIM_IT_EVNT_ROOT, suffix_evnt_tim,
                                                                't_eFMKTIM_InterruptLineEvnt', 0, "Number of Event Purpose Interrupt Line",
                                                                description_evnt_tim)
        
        enum_it_lines_dac = cls.code_gen.make_enum_from_variable(ENUM_FMKTIM_IT_DAC_ROOT, suffix_dac_tim,
                                                                't_eFMKTIM_InterruptLineDAC', 0, "Number of DAC Purpose Interrupt Line",
                                                                description_dac_tim)

        enum_timer = cls.code_gen.make_enum_from_variable(ENUM_FMKTIM_TIMER_ROOT, timer_number_a,
                                                           "t_eFMKTIM_Timer", 0, "Number of timer enable in smt32xxx board",
                                                           [f"Reference for HAL timer{timer_cfg[0][3:]}, this timer has {timer_cfg[1]} channel(s)" for timer_cfg in timer_cfg_a][1:])
        
        #-----------------------------------------------------------
        #------------code genration for FMKTIM module---------------
        #-----------------------------------------------------------
        #---------------------For FMKTIM_Config Public---------------------#

        print('[INFO] : FMKTIM_Codegen -> Config Public Code Generation')
        cls.code_gen.change_target_balise(TARGET_T_ENUM_START_LINE,TARGET_T_ENUM_END_LINE)
        cls.code_gen._write_into_file(enum_it_lines_dac, FMKTIM_CFGPUBLIC)
        cls.code_gen._write_into_file(enum_it_lines_evnt, FMKTIM_CFGPUBLIC)
        cls.code_gen._write_into_file(enum_it_lines_gp, FMKTIM_CFGPUBLIC)

        print('[INFO] : FMKTIM_Codegen -> Config Private Code Generation')
        cls.code_gen.change_target_balise(TARGET_T_ENUM_START_LINE,TARGET_T_ENUM_END_LINE)
        cls.code_gen._write_into_file(enum_channel, FMKTIM_CFGPRIVATE)
        cls.code_gen._write_into_file(enum_timer, FMKTIM_CFGPRIVATE)
        cls.code_gen.change_target_balise(TARGET_TIMER_CHNLNB_START, TARGET_TIMER_CHNLNB_END)
        cls.code_gen._write_into_file(def_tim_max_chnl, FMKTIM_CFGPRIVATE)
        cls.code_gen.change_target_balise(TARGET_T_VARIABLE_START_LINE, TARGET_T_VARIABLE_END_LINE)
        cls.code_gen._write_into_file(var_tim_max_chnl, FMKTIM_CFGPRIVATE)
        cls.code_gen._write_into_file(const_mapp_chnl_itline, FMKTIM_CFGPRIVATE)
        cls.code_gen._write_into_file(const_mapp_dac_tim, FMKTIM_CFGPRIVATE)
        cls.code_gen._write_into_file(const_mapp_evnt_tim, FMKTIM_CFGPRIVATE)
        cls.code_gen._write_into_file(const_mapp_gp_tim, FMKTIM_CFGPRIVATE)
        cls.code_gen._write_into_file(var_timcfg, FMKTIM_CFGPRIVATE)
        cls.code_gen.change_target_balise(TARGET_TIMER_X_IRQH_START, TARGET_TIMER_X_IRQH_END)
        cls.code_gen._write_into_file(func_imple, FMKTIM_CFGPRIVATE) 

        

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
    def get_itline_from_timcnl(cls, enum_timer:str, enum_channel:str)->str:
        timer_chnl = enum_timer + enum_channel

        try: 
            retval_itline = cls.itline_timchnl_mapping[timer_chnl]
        except(KeyError):
            raise KeyError(f'Cannot found Interrupt line for {enum_timer} and {enum_channel}')
        
        return retval_itline
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

