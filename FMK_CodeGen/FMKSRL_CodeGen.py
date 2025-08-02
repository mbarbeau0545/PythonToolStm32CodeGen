"""
#  @file        FMKSRL_CodeGen.py
#  @brief       Make Code Generation for the Module FMKSRL.
#
#  @author      mba
#  @date        08/01/2025
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
from PyCodeGene import LoadConfig_FromExcel as LCFE, TARGET_T_END_LINE,TARGET_T_ENUM_END_LINE, \
                                                    TARGET_T_ENUM_START_LINE,TARGET_T_START_LINE,TARGET_T_VARIABLE_START_LINE,\
                                                    TARGET_T_VARIABLE_END_LINE,TARGET_T_STRUCT_START_LINE,\
                                                    TARGET_T_STRUCT_END_LINE, TARGET_VARIABLE_END_LINE, TARGET_VARIABLE_START_LINE

from .FMKCPU_CodeGen import ENUM_FMKCPU_DMARQST
#------------------------------------------------------------------------------
#                                       CONSTANT
#------------------------------------------------------------------------------
ENUM_FMKSRL_LINE = 'FMKSRL_SERIAL_LINE'
ENUM_FMKSRL_HW_PROT = 'FMKSRL_HW_PROTOCOL'

TARGET_BUFF_MAPP_START = '    /* CAUTION : Automatic generated code section for Buffer Mapping: Start */\n'
TARGET_BUFF_MAPP_END =   '    /* CAUTION : Automatic generated code section for Buffer Mapping: End */\n'
TARGET_IRQN_HDLR_START = '    /* CAUTION : Automatic generated code section for UART/USART IRQHandler: Start */\n'
TARGET_IRQN_HDLR_END = '    /* CAUTION : Automatic generated code section for UART/USART IRQHandler: End */\n'

# CAUTION : Automatic generated code section: Start #

# CAUTION : Automatic generated code section: End #
#------------------------------------------------------------------------------
#                                       CLASS
#------------------------------------------------------------------------------

class FMKSRL_CodeGen():
    """
        Make code generation for FMKCPU module which include 
        file FMKSRL_ConfigPublic.h : 
            - Enum pour toutes les serial Lines UART/USART                               
            
        file FMKSRL_ConfigPrivate.h :
            - Mapping between Serial Line and Instance


        file  FMKSRL.c
            - variable SrlInfo
            - Rx/Tx buffer for each serial Line
            - Link between Rx/Tx Buffer and Serial Line
            - Irqn Handler
    """
    code_gen = LCFE()

    @classmethod
    def code_genration(cls, f_hw_cfg) -> None:

        # load array needed
        cls.code_gen.load_excel_file(f_hw_cfg)

        info_array = cls.code_gen.get_array_from_excel('FMKSRL_INFO')[1:]
       
        enm_srline = ''
        cst_mapp_istnc = ''
        var_srl_info = ''
        irqn_hdlr = ''
        var_RxTx_buffer = ''
        #----------------------------------------------------------------
        #-------------------------------Make Enum -----------------------
        #----------------------------------------------------------------
        max_line = len(info_array)
        enm_srline = cls.code_gen.make_enum_from_variable(ENUM_FMKSRL_LINE, [idx for idx in range(1, (max_line + 1))],
                                                            't_eFMKSRL_SerialLine', 0,
                                                            "Enum for Serial Line Available on CPU",
                                                            [f'Reference to Hardware Instance {info_line[0]}' for info_line in info_array])
        
        #----------------------------------------------------------------
        #----------------------------Make Mapping LINE to UART/USART --------------
        #----------------------------------------------------------------
        cst_mapp_istnc += '    /**\n' \
                        +    '    * @brief Mapping between Serial Line And Bsp Handle Typedef\n' \
                        +    '    */\n' \
                        + f'    USART_TypeDef * c_FmkSrl_BspInitIstcMapp_pas[{ENUM_FMKSRL_LINE}_NB]' +  ' = {\n'
        var_srl_info += '    /**< Store the Serial Configuration */\n' \
                     + f'    const t_sFMKSRL_SerialCfg c_FmkSrl_SerialCfg_as[{ENUM_FMKSRL_LINE}_NB]' + ' = {\n'
        tx_size_buff = 0
        rx_size_buff = 0
        is_istce_used = True
        for idx, line_info  in enumerate(info_array):
            idx_line = int(idx+1)

            # code generation for Var Tx/Rx Buffer
            # Buffer Size equals 0 if user didn't set it
            if line_info[2] == None or str(line_info[3]) == '0':
                rx_size_buff = 0
                is_istce_used = False
            else:
                is_istce_used = True
                rx_size_buff = line_info[2]

            if line_info[3] == None or str(line_info[3]) == '0':
                tx_size_buff = 0
                is_istce_used = False
            else:
                is_istce_used = True
                tx_size_buff = line_info[3]

            var_RxTx_buffer += f'    //--------- Tx, Rx Buffer for Serial Line {idx_line} ---------//\n' \
                            + f'    t_uint8 g_SrlLine_{idx_line}_RxBuffer_ua8[{rx_size_buff}];\n' \
                            + f'    t_uint8 g_SrlLine_{idx_line}_TxBuffer_ua8[{tx_size_buff}];\n' \
                            + '\n'
            
            # code generation for mapping instance
            cst_mapp_istnc += f'        {line_info[0]},' \
                            + ' ' * (SPACE_VARIABLE - len(f'{line_info[0]}')) \
                            + f' // Reference to Serial Line {idx_line} \n'
                            
            # code generation for Serial info
            var_srl_info += f'        [{ENUM_FMKSRL_LINE}_{idx_line}]' + ' = {\n' \
                            + f'            .c_clockPort_e = {ENUM_FMKCPU_RCC_ROOT}_{line_info[0]},\n' \
                            + f'            .c_HwType_e    = {ENUM_FMKSRL_HW_PROT}_{str(line_info[0])[:-1]},\n' \
                            + f'            .c_IRQNType_e  = {ENUM_FMKCPU_NVIC_ROOT}_{line_info[0]}_IRQN,\n'
            
            if is_istce_used:
                var_srl_info +=  f'            .c_DmaRqstRx   = {ENUM_FMKCPU_DMARQST}_{line_info[0]}_RX,\n' \
                                + f'            .c_DmaRqstTx   = {ENUM_FMKCPU_DMARQST}_{line_info[0]}_TX,\n' 
            else: 
                var_srl_info +=  f'            .c_DmaRqstRx   = (t_eFMKCPU_DmaRqst)0xFF,\n' \
                             + f'            .c_DmaRqstTx   = (t_eFMKCPU_DmaRqst)0xFF,\n' 
            var_srl_info    += f'            .Rx_StartAddressBuffer_pu8 = (t_uint8 *)(&g_SrlLine_{idx_line}_RxBuffer_ua8[0]),\n'\
                            +  f'            .Rx_bufferSize_u16 = (t_uint16){rx_size_buff},\n'\
                            +  f'            .Tx_StartAddressBuffer_pu8 = (t_uint8 *)(&g_SrlLine_{idx_line}_TxBuffer_ua8[0]),\n'\
                            +  f'            .Tx_bufferSize_u16 = (t_uint16){tx_size_buff},\n'
            var_srl_info   +=  '        },\n'
            
            
            #code generation for IRQN Handler
            irqn_hdlr += (
                    f'    void {line_info[1]}(void)\n'
                    '    {\n'
                    '        UART_HandleTypeDef * uartHandle_ps = NULL;\n'
                    '        USART_HandleTypeDef * usartHandle_ps = NULL;\n\n'
                    f'        FMKSRL_PRIVATE_GetHandleTypeDef(FMKSRL_SERIAL_LINE_{idx_line}, '
                    '&uartHandle_ps, &usartHandle_ps);\n\n'
                    '        if(uartHandle_ps != (UART_HandleTypeDef *)NULL)\n'
                    '        {\n'
                    '            HAL_UART_IRQHandler((UART_HandleTypeDef *)(uartHandle_ps));\n'
                    '        }\n'
                    '        else if(usartHandle_ps != (USART_HandleTypeDef *)NULL)\n'
                    '        {\n'
                    '            HAL_USART_IRQHandler((USART_HandleTypeDef *)(usartHandle_ps));\n'
                    '        }\n'
                    '    }\n\n'
                )
            
            # code generation for buffer-serial_line mapping


                        
        var_srl_info += '    };\n'
        cst_mapp_istnc += '    };\n\n'
        
                 
        #-----------------------------------------------------------
        #------------code genration for FMKCPU module---------------
        #-----------------------------------------------------------
        print('[INFO] : FMKSRL_Codegen -> Config Public Code Generation')
        cls.code_gen.change_target_balise(TARGET_T_ENUM_START_LINE, TARGET_T_ENUM_END_LINE)
        cls.code_gen._write_into_file(enm_srline, FMKSRL_CFGPUBLIC)

        print('[INFO] : FMKSRL_Codegen -> Config Private Code Generation')
        cls.code_gen.change_target_balise(TARGET_T_VARIABLE_START_LINE, TARGET_T_VARIABLE_END_LINE)
        cls.code_gen._write_into_file(cst_mapp_istnc, FMKSRL_CFGPRIVATE)
        cls.code_gen._write_into_file(var_srl_info, FMKSRL_CFGPRIVATE)
        cls.code_gen._write_into_file(var_RxTx_buffer, FMKSRL_CFGPRIVATE)
        cls.code_gen.change_target_balise(TARGET_IRQN_HDLR_START, TARGET_IRQN_HDLR_END)
        cls.code_gen._write_into_file(irqn_hdlr, FMKSRL_CFGPRIVATE)

        

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

