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
from PythonToolCfg.FMK_PATH import *
from .FMKCPU_CodeGen import ENUM_FMKCPU_DMARQST
from PyCodeGene import LoadConfig_FromExcel as LCFE, TARGET_T_END_LINE,TARGET_T_ENUM_END_LINE, \
                                                    TARGET_T_ENUM_START_LINE,TARGET_T_START_LINE,TARGET_T_VARIABLE_START_LINE,\
                                                    TARGET_T_VARIABLE_END_LINE,TARGET_T_STRUCT_START_LINE,\
                                                    TARGET_T_STRUCT_END_LINE
#------------------------------------------------------------------------------
#                                       CONSTANT
#------------------------------------------------------------------------------
TARGET_ADC_SWITCH_START = "            /* CAUTION : Automatic generated code section for switch_case ADC channel: Start */\n"
TARGET_ADC_SWITCH_END   = "            /* CAUTION : Automatic generated code section for switch_case ADC channel: End */\n"
TARGET_ADC_CHNLNB_START = "    /* CAUTION : Automatic generated code section for ADC channels number: Start */\n"
TARGET_ADC_CHNLNB_END   = "    /* CAUTION : Automatic generated code section for ADC channels number: End */\n"
TARGET_ADC_X_IRQN_START = "    /* CAUTION : Automatic generated code section for ADCx IRQN_Handler: Start */\n"
TARGET_ADC_X_IRQN_END =   "    /* CAUTION : Automatic generated code section for ADCx IRQN_Handler: End */\n"
# CAUTION : Automatic generated code section: Start #

# CAUTION : Automatic generated code section: End #
#------------------------------------------------------------------------------
#                                       CLASS
#------------------------------------------------------------------------------
class FMKCDA_CodeGen():
    """
        Make code generation for FMKCDA module which include 
        file FMKCDA_ConfigPublic.h : 
            - Enum Adc Channel                                
            - Enum Adc              
            - enum adc internal TS_CAL_1, SUPPLY_VOLTAGE etc                   
        
        file FMKCDA_ConfigPrivate.h :
            define ADC_x max channel
            variable ADCx max channel
            define for Vref Calibration address
            define for temp calib address 
            variable for Vref Calibration access per adc


        file  FMK_CDA.c
            - variable g_AdcInfo_as init 
            - varaible for scan mode counter rank              
            - switch case Adc channel to bsp channel 
    """
    code_gen = LCFE()

    @classmethod
    def code_genration(cls, f_hw_cfg) -> None:
        # load array needed
        cls.code_gen.load_excel_file(f_hw_cfg)
        #irqn_cfg_a = cls.code_gen.get_array_from_excel("GI_IRQN")
        adc_astr   = cls.code_gen.get_array_from_excel("GI_ADC")[1:]
        dac_astr   = cls.code_gen.get_array_from_excel("GI_DAC")[1:]
        vref_astr  = cls.code_gen.get_array_from_excel("FMKCDA_VoltageRef")[1:]
        calib_astr = cls.code_gen.get_array_from_excel("FMKCDA_CalibrationOthers")[1:]
        list_irqn  = cls.code_gen.get_array_from_excel('FMKCDA_IRQNHandler')
        enum_adc = ""
        enum_adc_channel = ""
        switch_adc_channel = ""
        var_adc_cfg = ""
        var_hw_vref = ""
        enum_other_calib = ""
        def_other_calib = ""
        var_other_calib = ""
        def_vref_calib = ""
        var_other_cfg = ""
        var_vref_calib = ""
        var_rank_counter = ""
        func_irqn = ''
        var_adc_max_channel = ""
        def_adcx_max_channel = ""
        max_adc_channel: int = 0
        #----------------------------------------------------------------
        #-----------------------------make adc enum----------------------
        #-----------------------------------------------------------------
        enum_adc = cls.code_gen.make_enum_from_variable(ENUM_ADC_ISCT_ROOT, [str(adc_info[0][4:]) for adc_info in adc_astr],
                                                          "t_eFMKCDA_Adc", 0 , "Nmber of ADC in this harware",
                                                          [f"Reference to HAL ADC{adc_info[0][4:]}" for adc_info in adc_astr])
        #----------------------------------------------------------------
        #---------------make adc intern channel enum----------------------
        #-----------------------------------------------------------------
        enum_internal_other = []
        for adc_intern in calib_astr:
            #idx_enum = str(adc_intern[0]).index("_")
            enum_internal_other.append(adc_intern[0])
        enum_other_calib = cls.code_gen.make_enum_from_variable(ENUM_ADC_INTERN_SENSOR, enum_internal_other,
                                                                "t_eFMKCDA_AdcInternSns", 0, "Internal Sensors manage by the cpu",
                                                                 [f"Refernce to {str(calib_astr[0])}" for calib_astr in calib_astr] )

        #----------------------------------------------------------------
        #-----------------------------make adc channel enum--------------
        #--------------------------make adc channel max define-----------
        #-------------------------------make adc info--------------------
        #-----------------------------------------------------------------
        var_adc_cfg += "    /**< Variable for Adc Config */\n" \
                        +"    const t_sFMKCDA_AdcCfg c_FmkCda_AdcCfg_as[FMKCDA_ADC_NB] = {\n"
        var_rank_counter += "/**< Rank for each channel add for ADC */\n"\
                            + "t_uint8 g_counterRank_au8[FMKCDA_ADC_NB] = {\n"
        var_adc_max_channel += "    /**< Variable for Adc Max channel*/\n" \
                            + "    const t_uint8 c_FmkCda_AdcMaxChnl_ua8[FMKCDA_ADC_NB] = {\n"
        for adc_info in adc_astr:
            adc_index = adc_info[0][4:]
            # know the max adc channel
            if(adc_info[1] > max_adc_channel):
                max_adc_channel = int(adc_info[1])
            # make define max ADCx channel
            def_adcx_max_channel += f"    #define FMKCDA_ADC_{adc_index}_MAX_CHANNELS ((t_uint8){adc_info[1]})\n"
            #make adc info
            var_adc_cfg +=f"        [FMKCDA_ADC_{adc_index}] =" + " {\n" \
                        + f"            .adcTypedef_ps = ADC{adc_index},\n" \
                        + f"            .c_clock_e = {ENUM_FMKCPU_RCC_ROOT}_{str(adc_info[3]).upper()},\n" \
                        + f"            .c_IRQNType_e = {ENUM_FMKCPU_NVIC_ROOT}_{str(adc_info[2]).upper()},\n" \
                        + f'            .c_DmaAdc_e = {ENUM_FMKCPU_DMARQST}_ADC{adc_index},\n'\
                        + "        },\n"
            #make rank coutner 
            var_rank_counter += "    (t_uint8)0,\n"
            # make variable adc maxchannel
            var_adc_max_channel += f"        (t_uint8)FMKCDA_ADC_{adc_index}_MAX_CHANNELS,\n"

        var_adc_max_channel += "    };\n\n"
        var_adc_cfg += "    };\n\n"
        var_rank_counter += "};\n\n"
        enum_adc_channel = cls.code_gen.make_enum_from_variable(ENUM_ADC_CHNL_ROOT, [int(idx) for idx in range(max_adc_channel)],
                                                                "t_eFMKCDA_AdcChannel", 0 , " Number of channel in ADC Instances",
                                                                  [f"Reference to HAL adc channel {int(idx)}" for idx in range(max_adc_channel)])

        #----------------------------------------------------------------
        #-----------------------------Make IRQNHandler-------------------
        #----------------------------------------------------------------
        for adc_irqn in list_irqn[1:]:
            func_irqn += '    /*********************************\n' \
                        + f'     * {adc_irqn[0]}\n' \
                        + '    *********************************/\n' \
                        + f'    void {adc_irqn[0]}(void)\n' \
                        + '    {\n'  
            list_adc_asso = str(adc_irqn[1]).split(',')
            for adc_asso in list_adc_asso:
                adc_asso = adc_asso.replace(' ', '')
                func_irqn += '        HAL_ADC_IRQHandler(FMKCDA_PRIVATE_GetHandleTypeDef(' \
                            + f'{ENUM_ADC_ISCT_ROOT}_{adc_asso[-1]}));\n'\
                            
            func_irqn += '        return;\n'         
            func_irqn += '    }\n'
        #----------------------------------------------------------------
        #-----------------------------make channel switch case-----------
        #-----------------------------------------------------------------
        for idx in range(max_adc_channel):
            switch_adc_channel += f"            case {ENUM_ADC_CHNL_ROOT}_{int(idx)}:\n" \
                                 + f"                *f_bspChannel_32 = ADC_CHANNEL_{idx};\n" \
                                 + f"                break;\n"
        #-----------------------------------------------------------
        #------------make define/ var for vref----------------------
        #-----------------------------------------------------------
        var_hw_vref += "    /**< Variable for Hardware configuration adc and channel for Voltage Reference for each adc */\n"
        var_hw_vref += "    const t_sFMKCDA_HwAdcCfg c_FmkCda_HwVrefCfg[FMKCDA_ADC_NB] = {\n"
        var_vref_calib += "    /**<     Variable for voltage ref calibration value */\n"
        var_vref_calib += "    const volatile t_uint16* c_FmkCda_VrefCalibAddress_pas16[FMKCDA_ADC_NB] = {\n"
        for idx, vref_info in enumerate(vref_astr):
            def_vref_calib += f"    #define {ENUM_ADC_INTERN_SENSOR}_{vref_info[0]}_ADDRESS ((volatile t_uint16 *){str(vref_info[1])})\n"

            var_vref_calib += f"        (volatile t_uint16 *){ENUM_ADC_INTERN_SENSOR}_{vref_info[0]}_ADDRESS," \
                            + " " * (60 - len(str(f"{ENUM_ADC_INTERN_SENSOR}_{vref_info[0]}_ADDRESS"))) \
                            + f"// {ENUM_ADC_ISCT_ROOT}_{str(adc_astr[idx][0])[4:]}\n"

            var_hw_vref += "        {" \
                        + f"{ENUM_ADC_ISCT_ROOT}_{str(vref_info[2])[4:]}," \
                        + " " * (SPACE_VARIABLE - len(str(vref_info[2]))) \
                        + f"{ENUM_ADC_CHNL_ROOT}_{str(vref_info[3])[12:]}" + "},"\
                        + " " * (SPACE_VARIABLE - len(str(vref_info[3]))) \
                        + f"// for {ENUM_ADC_ISCT_ROOT}_{str(adc_astr[idx][0])[4:]}\n" 
            
        var_vref_calib += "    };\n\n"
        var_hw_vref += "    };\n\n"
        #-----------------------------------------------------------
        #------------make define/ var for interna sensors-----------
        #-----------------------------------------------------------
        var_other_cfg   += "    /**< Variable for Interna Sensors configuration*/\n"
        var_other_cfg   += f"    const t_sFMKCDA_ADcInternalSnsCfg c_FmkCda_HwInternalSnsCfg_as[{ENUM_ADC_INTERN_SENSOR}_NB] =" + "{\n"
        var_other_calib += "    /**< Variable for Internal Sensors Calibration address */\n"
        var_other_calib += "    const volatile t_uint16* c_FmkCda_HwInternalSnsAddress_pau16[FMKCDA_ADC_INTERN_NB] = {\n"
        for idx, other_calib_info in enumerate(calib_astr):
            def_other_calib += f"    #define {ENUM_ADC_INTERN_SENSOR}_{other_calib_info[0]}_ADDRESS ((volatile t_uint16*){str(other_calib_info[1])})\n"

            var_other_calib += f"        (volatile t_uint16 *){ENUM_ADC_INTERN_SENSOR}_{other_calib_info[0]}_ADDRESS,"  \
                            + " " * (60 - len(str(f"{ENUM_ADC_INTERN_SENSOR}_{other_calib_info[0]}_ADDRESS"))) \
                            + f"// {ENUM_ADC_INTERN_SENSOR}_{enum_internal_other[idx]}\n"
            if str(other_calib_info[4]).upper() not in ['TRUE', 'FALSE']:
                raise ValueError('Expected TRUE or FALSE, get %d', other_calib_info[4])
            var_other_cfg += "        {" + '{' \
                        + f"{ENUM_ADC_ISCT_ROOT}_{str(other_calib_info[2])[4:]}," \
                        + " " * (SPACE_VARIABLE - len(str(other_calib_info[2]))) \
                        + f"{ENUM_ADC_CHNL_ROOT}_{str(other_calib_info[3])[12:]}" + "},"\
                        + " " * (SPACE_VARIABLE - len(str(other_calib_info[3]))) \
                        + f"{str(other_calib_info[4]).upper()}"\
                        + " " * (SPACE_VARIABLE - len(str(other_calib_info[4]))) \
                        + '},'\
                        + f"// for {ENUM_ADC_INTERN_SENSOR}_{enum_internal_other[idx]}\n" 
            
        var_other_cfg  += "    };\n\n"
        var_other_calib += "    };\n\n"
        #-----------------------------------------------------------
        #------------code genration for FMKADC module---------------
        #-----------------------------------------------------------
        
        print('[INFO] : FMKCDA -> Config Public Code generation')
        cls.code_gen.change_target_balise(TARGET_T_ENUM_START_LINE, TARGET_T_ENUM_END_LINE)
        cls.code_gen._write_into_file(enum_adc_channel, FMKCDA_CONFIGPUBLIC)
        cls.code_gen._write_into_file(enum_adc, FMKCDA_CONFIGPUBLIC)
        cls.code_gen._write_into_file(enum_other_calib,FMKCDA_CONFIGPUBLIC)


        print('[INFO] : FMKCDA -> Config Private Code generation')
        cls.code_gen.change_target_balise(TARGET_ADC_CHNLNB_START, TARGET_ADC_CHNLNB_END)
        cls.code_gen._write_into_file(def_adcx_max_channel, FMKCDA_CONFIGPRIVATE)
        cls.code_gen._write_into_file(def_other_calib, FMKCDA_CONFIGPRIVATE)
        cls.code_gen._write_into_file(def_vref_calib, FMKCDA_CONFIGPRIVATE)
        cls.code_gen.change_target_balise(TARGET_T_VARIABLE_START_LINE, TARGET_T_VARIABLE_END_LINE)
        cls.code_gen._write_into_file(var_other_calib, FMKCDA_CONFIGPRIVATE)
        cls.code_gen._write_into_file(var_other_cfg, FMKCDA_CONFIGPRIVATE)
        cls.code_gen._write_into_file(var_hw_vref, FMKCDA_CONFIGPRIVATE)
        cls.code_gen._write_into_file(var_vref_calib, FMKCDA_CONFIGPRIVATE)
        cls.code_gen._write_into_file(var_adc_max_channel, FMKCDA_CONFIGPRIVATE)
        cls.code_gen._write_into_file(var_adc_cfg, FMKCDA_CONFIGPRIVATE)
        cls.code_gen.change_target_balise(TARGET_ADC_X_IRQN_START, TARGET_ADC_X_IRQN_END)
        cls.code_gen._write_into_file(func_irqn, FMKCDA_CONFIGPRIVATE)

        print('[INFO] : FMKCDA -> Config Specific Code generation')
        cls.code_gen.change_target_balise(TARGET_ADC_SWITCH_START, TARGET_ADC_SWITCH_END)
        cls.code_gen._write_into_file(switch_adc_channel, FMKCDA_CONFIG_SPEC)

        

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

