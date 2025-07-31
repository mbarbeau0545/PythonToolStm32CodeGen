"""
#  @file        FMKFDCAN_CodeGen.py
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

from typing import List,Dict
#------------------------------------------------------------------------------
#                                       CONSTANT
#------------------------------------------------------------------------------

TARGET_CAN_IRQN_HANDLER_START = '    /* CAUTION : Automatic generated code section for FDCAN IRQN Handler : Start */\n'
TARGET_CAN_IRQN_HANDLER_END   = '    /* CAUTION : Automatic generated code section for FDCAN IRQN Handler : End */\n'

# CAUTION : Automatic generated code section: Start #

# CAUTION : Automatic generated code section: End #
#------------------------------------------------------------------------------
#                                       CLASS
#------------------------------------------------------------------------------

class FMKFDCAN_CodeGen():
    """
        Make code generation for FMKCPU module which include 
        file FMKSRL_ConfigPublic.h : 
            - Node list                               
            
        file FMKSRL_ConfigPrivate.h :
            - NodeCfg 
            - IRQN Handler



    """
    code_gen = LCFE()

    @classmethod
    def code_genration(cls, f_hw_cfg) -> None:
        cls.code_gen.load_excel_file(f_hw_cfg)
        arr_irqn_cfg = cls.code_gen.get_array_from_excel('fdcan_irqn_handler')
        arr_node_cfg = cls.code_gen.get_array_from_excel('Fdcan_Info')

        idx_node_list:List[str] = [ str(idx + 1) for idx in range(0, len(arr_node_cfg[1:]))]
        # make enum node 
        node_cfg_codgen:str = ''
        buffer_codegen = ''
        irqn_codegen:str = ''
        enum_node = cls.code_gen.make_enum_from_variable('FMKFDCAN_NODE', idx_node_list,
                                                          't_eFMKFDCAN_NodeList', 0, 
                                                          'List of FDCAN nodes.', 
                                                          [f'Node {idx} Identifier' for idx in idx_node_list])
        
        for irqn_info in arr_irqn_cfg[1:]:
            irqn_func:str = irqn_info[0]

            try:
                idx_node:int = int(irqn_func[5])
            except TypeError:
                raise TypeError('Cannot found instance index in %d', irqn_func)
            
            irqn_codegen += (
                 '    /**********************************\n'
                f'    * {irqn_func}\n'
                 '    **********************************/\n'
                f'    void {irqn_func}(void)\n'
                 '    {\n'
                f'    HAL_FDCAN_IRQHandler(FMKFDCAN_PRIVATE_GetHandleTypeDef(FMKFDCAN_NODE_{idx_node}));\n'
                 '    return;\n'
                 '    }\n\n'
            )

        node_cfg_codgen += '    ///@brief Node configuraiton\n'\
                        + '    const t_sFMKFDCAN_NodeCfg c_FmkFdcan_NodeCfg_as[FMKFDCAN_NODE_NB] = {\n'
        for node_info in arr_node_cfg[1:]:
            idx_node = int(str(node_info[0])[-1])

            buffer_codegen += (
                f"    //--------- Tx, Rx Buffer for Can Node {idx_node} ---------//\n"
                f"    t_sFMKFDCAN_RxItemBuffer g_Node{idx_node}_RxBuffer_as[{node_info[2]}];\n"
                f"    t_sFMKFDCAN_TxItemBuffer g_Node{idx_node}_TxBuffer_as[{node_info[3]}];\n"
            )
            node_cfg_codgen += (
                f"        [FMKFDCAN_NODE_{idx_node}] = " + "{\n"
                f"            .Instance = {node_info[0]},\n"
                f"            .c_Clock_e = FMKCPU_RCC_CLK_{node_info[1]},\n"
                f"            .c_IrqnLine1_e = FMKCPU_NVIC_{node_info[0]}_IT0_IRQN,\n"
                f"            .c_IrqnLine2_e = FMKCPU_NVIC_{node_info[0]}_IT1_IRQN,\n"
                f"            .rxBufferStartAddress_pas = (t_sFMKFDCAN_RxItemBuffer *)(&g_Node{idx_node}_RxBuffer_as[0]),\n"
                f"            .rxBufferSize_u16 = (t_uint16){node_info[2]},\n"
                f"            .txBufferStartAddress_pas = (t_sFMKFDCAN_TxItemBuffer *)(&g_Node{idx_node}_TxBuffer_as[0]),\n"
                f"            .txBufferSize_u16 = (t_uint16){node_info[3]},\n"
                "        },\n"
            )
        buffer_codegen += '\n\n'
        node_cfg_codgen += '    };\n\n'

        print('[INFO] : FMKFDCAN_Codegen -> Config Public Code Generation')
        cls.code_gen.change_target_balise(TARGET_T_ENUM_START_LINE, TARGET_T_ENUM_END_LINE)
        cls.code_gen._write_into_file(enum_node, FMKFDCAN_CFG_PUBLIC)
        print('[INFO] : FMKFDCAN_Codegen -> Config Private Code Generation')
        cls.code_gen.change_target_balise(TARGET_T_VARIABLE_START_LINE, TARGET_T_VARIABLE_END_LINE)
        print('[INFO] : FMKFDCAN_Codegen -> Config Private Code Generation')
        cls.code_gen._write_into_file(node_cfg_codgen, FMKFDCAN_CFG_PRIVATE)
        cls.code_gen._write_into_file(buffer_codegen, FMKFDCAN_CFG_PRIVATE)
        cls.code_gen.change_target_balise(TARGET_CAN_IRQN_HANDLER_START, TARGET_CAN_IRQN_HANDLER_END)
        cls.code_gen._write_into_file(irqn_codegen, FMKFDCAN_CFG_PRIVATE)

        
        

        
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

