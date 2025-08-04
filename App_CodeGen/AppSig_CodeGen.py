"""
#  @file        AppSig_CodeGen.py
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
import shutil
from typing import Dict, List
from PyCodeGene import LoadConfig_FromExcel as LCFE, TARGET_T_END_LINE,TARGET_T_ENUM_END_LINE, \
                                                    TARGET_T_ENUM_START_LINE,TARGET_T_VARIABLE_START_LINE,\
                                                    TARGET_T_VARIABLE_END_LINE, TARGET_VARIABLE_END_LINE,TARGET_VARIABLE_START_LINE,\
                                                    TARGET_T_DEFINE_START, TARGET_T_DEFINE_END

import re
#------------------------------------------------------------------------------
#                                       CONSTANT
#------------------------------------------------------------------------------


PATTERN_ENUM = r'(\d+)="([^"]+)"'
PATTERN_SIGNAL = re.compile(
    r"Sig=(\w+)\s+unsigned\s+(\d+)"                  # nom et longueur
    r"(?:\s+(-m))?"                                  # encodage
    r"(?:\s+/f:(\d+))?"                              # factor
    r"(?:\s+/o:(\d+))?"                              # offset
    r"(?:\s+/max:(\d+))?"                            # max (non utilisé ici mais capturé)
    r"(?:\s+/e:(\w+))?"                              # enum
)

# Expressions régulières nécessaires
PATTERN_SYM_ID = re.compile(r'ID=([0-9A-Fa-f]+)h\s*//\s*(\w+)')
PATTERN_SYM_LEN = re.compile(r'Len=(\d+)')
PATTERN_SYM_SIG = re.compile(r'Sig=(\w+)\s+(\d+)')

MSG_TYPE_MAPPING = {
    'RECEIVE' : 'APPSIG_MSG_DIR_RX',
    'SEND' : 'APPSIG_MSG_DIR_TX',
    'SENDRECEIVE' : 'APPSIG_MSG_DIR_RX_TX',
}

SIG_SPACE_VARIABLE = 55
#------------------------------------------------------------------------------
#                                       CLASS
#------------------------------------------------------------------------------
class IdxSignal:
    lenght = 0
    enumlink = 1

class AppSig_CodeGen():
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
    enum:Dict[str, List[List[int]]] = {}
    signal:Dict[str, Dict]           = {}
    symbol:Dict[str, Dict]     = {}
    list_id = {
        'SRL' : [],
        'CAN' : []
    }
    file_cfg_path:str = ''

    @classmethod
    def code_generation(cls, f_msg_cfg_file:str) -> None:

        cls.file_cfg_path = f_msg_cfg_file
        cls.get_info_from_file()

        # make enum with signals 
    
        codgen_sigCfg = ''
        codegen_enum_msg_can = ''
        codegen_enum_sig = ''
        codegen_enum_msg_srl = ''
        codgen_srlmsg_dcode = ''
        codgen_canmsg_dcode = ''
        codgen_srlmsg_cfg = ''
        codgen_canmsg_cfg = ''
        codgen_def_srlid = ''
        codgen_def_canid = ''
        signals_list = list(cls.signal.keys())
        codegen_enum_sig += cls.code_gen.make_enum_from_variable('APPSIG_SIGNAL',
                                                                signals_list,
                                                                't_eAPPSIG_Signal',
                                                                0, 'Signal list available')
        
        # make enum for can msg & srl msg
        can_msg_list = [msg_name for msg_name, msg_info in cls.symbol.items()
                if msg_info['msg_type'] == 'CAN']
        
        srl_msg_list = [msg_name for msg_name, msg_info in cls.symbol.items()
                if msg_info['msg_type'] == 'SRL']

        codegen_enum_msg_can += cls.code_gen.make_enum_from_variable('APPSIG_CAN_MSG',
                                                                    can_msg_list,
                                                                    't_eAPPSIG_CanMsgList',
                                                                    0, 'message can available')
        
        codegen_enum_msg_srl += cls.code_gen.make_enum_from_variable('APPSIG_SRL_MSG',
                                                                    srl_msg_list,
                                                                    't_eAPPSIG_SrlMsgList',
                                                                    0, 'message serial available')
        
        codgen_sigCfg += '    ///@brief Signal Configuration\n'
        codgen_sigCfg += '    const t_sAPPSIG_SigCfg c_AppSig_SignalCfg_as[APPSIG_SIGNAL_NB] =' + ' {\n'

        for signal_name, signal_cfg in cls.signal.items():
            codgen_sigCfg += '        {'\
                            + f'(t_uint8){signal_cfg['length']},'\
                            + ' ' * ((SIG_SPACE_VARIABLE) - len(f"{signal_cfg['length']},"))\
                            + f'APPSIG_SIG_ENCODE_{str(signal_cfg['encoding']).upper()},'\
                            + ' ' * ((SIG_SPACE_VARIABLE) - len(f"{signal_cfg['encoding']},"))\
                            + f'(t_float32){signal_cfg['factor']}.0f,'\
                            + ' ' * ((SIG_SPACE_VARIABLE) - len(f"{signal_cfg['factor']},"))\
                            + f'(t_sint16){signal_cfg['offset']}'\
                            + ' ' * ((SIG_SPACE_VARIABLE) - len(f"{signal_cfg['offset']}"))\
                            + '},' + f'// APPSIG_SIGNAL_{str(signal_name).upper()}\n'
        codgen_sigCfg += '    };\n\n'

        codgen_canmsg_cfg += '    ///@brief CAN Message Information\n'\
                        + '    const t_sAPPSIG_MsgInfo c_AppSig_CanMsgCfg_as[APPSIG_CAN_MSG_NB] = {\n'\
                        +'    //  Identifier                                          Direction                                                CyclicSend                                                 TimeOut                                                         Sig Cfg                                         nbSignal\n'
        codgen_srlmsg_cfg += '    ///@brief Serial Message Information\n'\
                            + '    const t_sAPPSIG_MsgInfo c_AppSig_SrlMsgCfg_as[APPSIG_SRL_MSG_NB] = {\n'\
                            + '    //  Identifier                                          Direction                                                CyclicSend                                                 TimeOut                                                         Sig Cfg                                         nbSignal\n'
        codgen_def_srlid += '    ///@brief Serial Message Id\n'
        codgen_def_canid += '    ///@brief CAN Message Id\n'

        for msg_name, msg_cfg in cls.symbol.items():
            msgid_hexvalue = hex(int(msg_cfg['msg_id'], 16))

            if msg_cfg['msg_type'] == 'SRL':
                signal_number = len(msg_cfg['signals'].keys())
                codgen_srlmsg_dcode += f'    ///@brief Variable for decoding {msg_name}\n'\
                                    + f'    const t_sAPPSIG_MsgSignalsCfg c_AppSig_Srl_{msg_name}_as[{signal_number}] = ' + '{\n'
                
                for signal_name, signal_startbit in msg_cfg['signals'].items():
                    codgen_srlmsg_dcode += '    {'\
                                        + f'APPSIG_SIGNAL_{str(signal_name).upper()},'\
                                        + ' ' * ((SIG_SPACE_VARIABLE) - len(f"APPSIG_SIGNAL_{signal_name},"))\
                                        + f'(t_uint8){signal_startbit}'\
                                        + ' ' * ((SIG_SPACE_VARIABLE) - len(f"(t_uint8){signal_startbit}"))\
                                        + '},\n'
                codgen_srlmsg_dcode += '    };\n\n\n'

                # make define msg 
                codgen_def_srlid += f'    #define APPSIG_SRL_ID_{str(msg_name).upper()}'\
                                + ' '* ((SIG_SPACE_VARIABLE) - len(f"APPSIG_SRL_ID_{str(msg_name).upper()}"))\
                                + f'((t_uint32){msgid_hexvalue})\n'
                
                # make serial msg cfg
                codgen_srlmsg_cfg += '    {'\
                                    + f'APPSIG_SRL_ID_{str(msg_name).upper()},'\
                                    + ' ' * ((SIG_SPACE_VARIABLE) - len(f"APPSIG_SRL_ID_{str(msg_name).upper()}"))\
                                    + f'{MSG_TYPE_MAPPING[msg_cfg['msg_direction']]},'\
                                    + ' ' * ((SIG_SPACE_VARIABLE) - len(f"{MSG_TYPE_MAPPING[msg_cfg['msg_direction']]}"))\
                                    + f'(t_uint16){msg_cfg['cycle_time']},'\
                                    + ' ' * ((SIG_SPACE_VARIABLE) - len(f"(t_uint16){msg_cfg['cycle_time']}"))\
                                    + f'(t_uint16){msg_cfg['timeout']},'\
                                    + ' ' * ((SIG_SPACE_VARIABLE) - len(f"(t_uint16){msg_cfg['timeout']}"))\
                                    + f'c_AppSig_Srl_{msg_name}_as,'\
                                    + ' ' * ((SIG_SPACE_VARIABLE) - len(f"c_AppSig_Srl_{msg_name}_as"))\
                                    + f'(t_uint8){signal_number}' + '},'\
                                    + f' // APPSIG_SRL_{str(msg_name).upper()}\n'
                                     
                                    
            elif msg_cfg['msg_type'] == 'CAN':
                signal_number = len(msg_cfg['signals'].keys())
                codgen_canmsg_dcode += f'    ///@brief Variable for decoding {str(signal_name).upper()}\n'\
                                    + f'    const t_sAPPSIG_MsgSignalsCfg c_AppSig_Can_{msg_name}_as[{signal_number}] = ' + '{\n'
                
                for signal_name, signal_startbit in msg_cfg['signals'].items():
                    codgen_canmsg_dcode += '    {'\
                                        + f'APPSIG_SIGNAL_{str(signal_name).upper()},'\
                                        + ' ' * ((SIG_SPACE_VARIABLE) - len(f"APPSIG_SIGNAL_{signal_name},"))\
                                        + f'(t_uint8){signal_startbit}'\
                                        + ' ' * ((SIG_SPACE_VARIABLE) - len(f"(t_uint8){signal_startbit}"))\
                                        + '},\n'
                codgen_canmsg_dcode += '    };\n\n\n'

                # make define msg 
                codgen_def_canid += f'    #define APPSIG_CAN_ID_{str(msg_name).upper()}'\
                                + ' '* ((SIG_SPACE_VARIABLE) - len(f"APPSIG_CAN_ID_{msg_name}"))\
                                + f'((t_uint32){msgid_hexvalue})\n'
            
                codgen_canmsg_cfg += '    {'\
                                    + f'APPSIG_CAN_ID_{str(msg_name).upper()},'\
                                    + ' ' * ((SIG_SPACE_VARIABLE) - len(f"APPSIG_CAN_ID_{msg_name}"))\
                                    + f'{MSG_TYPE_MAPPING[msg_cfg['msg_direction']]},'\
                                    + ' ' * ((SIG_SPACE_VARIABLE) - len(f"{MSG_TYPE_MAPPING[msg_cfg['msg_direction']]}"))\
                                    + f'(t_uint16){msg_cfg['cycle_time']},'\
                                    + ' ' * ((SIG_SPACE_VARIABLE) - len(f"(t_uint16){msg_cfg['cycle_time']}"))\
                                    + f'(t_uint16){msg_cfg['timeout']},'\
                                    + ' ' * ((SIG_SPACE_VARIABLE) - len(f"(t_uint16){msg_cfg['timeout']}"))\
                                    + f'c_AppSig_Can_{msg_name}_as,'\
                                    + ' ' * ((SIG_SPACE_VARIABLE) - len(f"c_AppSig_Can_{msg_name}_as"))\
                                    + f'(t_uint8){signal_number}' + '},'\
                                    + f' // APPSIG_CAN_{str(msg_name).upper()}\n'
                
            else:
                raise ValueError(f'Unknown type of message {msg_cfg['msg_type']}')
        codgen_srlmsg_cfg += '    };\n\n'
        codgen_canmsg_cfg += '    };\n\n'

        print('[INFO] : APPSIG_Codegen -> Config Public Code Generation')
        cls.code_gen.change_target_balise(TARGET_T_ENUM_START_LINE, TARGET_T_ENUM_END_LINE)
        cls.code_gen._write_into_file(codegen_enum_msg_can, APPSIG_CFG_PUBLIC)
        cls.code_gen._write_into_file(codegen_enum_msg_srl, APPSIG_CFG_PUBLIC)
        cls.code_gen._write_into_file(codegen_enum_sig, APPSIG_CFG_PUBLIC)

        print('[INFO] : APPSIG_Codegen -> Config Private Code Generation')
        cls.code_gen.change_target_balise(TARGET_T_DEFINE_START, TARGET_T_DEFINE_END)
        cls.code_gen._write_into_file(codgen_def_canid, APPSIG_CFG_PRIVATE)
        cls.code_gen._write_into_file(codgen_def_srlid, APPSIG_CFG_PRIVATE)
        cls.code_gen.change_target_balise(TARGET_T_VARIABLE_START_LINE, TARGET_T_VARIABLE_END_LINE)
        cls.code_gen._write_into_file(codgen_canmsg_cfg, APPSIG_CFG_PRIVATE)
        cls.code_gen._write_into_file(codgen_srlmsg_cfg, APPSIG_CFG_PRIVATE)
        cls.code_gen._write_into_file(codgen_canmsg_dcode, APPSIG_CFG_PRIVATE)
        cls.code_gen._write_into_file(codgen_srlmsg_dcode, APPSIG_CFG_PRIVATE)
        cls.code_gen._write_into_file(codgen_sigCfg, APPSIG_CFG_PRIVATE)
        
        
        





        # make python varaible 
    @classmethod
    def get_info_from_file(cls):
        """
            @brief get enum, signal, symbol from .sym 
        """
        current_read = 'NONE'
        waiting_for_timeout = False
        current_id = None
        current_type = None
        current_len = None
        current_symbol = None

        with open(cls.file_cfg_path, 'r') as file:
            for line in file.readlines():
                line = line.strip()

                if "ENUMS" in line:
                    current_read = 'ENUMS'
                    continue
                elif "SIGNALS" in line:
                    current_read = 'SIGNALS'
                    continue
                elif "SENDRECEIVE" in line:
                    current_read = 'SENDRECEIVE'
                    continue
                elif "RECEIVE" in line:
                    current_read = 'RECEIVE'
                    continue
                elif "SEND" in line:
                    current_read = 'SEND'
                    continue

                match current_read:
                    case 'ENUMS':
                        if 'Enum=' in line:
                            start_index = line.index('Enum=') + len('Enum=')
                            end_index = line.index('(')
                            enum_name = line[start_index:end_index]
                            resultats = re.findall(PATTERN_ENUM, line)
                            pairs = [[int(index), value] for index, value in resultats]
                            cls.enum[enum_name] = pairs

                    case 'SIGNALS':
                        match = PATTERN_SIGNAL.match(line)
                        if match:
                            nom_signal    = match.group(1)
                            longueur      = int(match.group(2))
                            encoding_flag = match.group(3)
                            factor        = int(match.group(4)) if match.group(4) else 1
                            offset        = int(match.group(5)) if match.group(5) else 0
                            # match.group(6) = max (non utilisé ici)
                            enum_name     = match.group(7) if match.group(7) else None

                            encoding = "MOTOROLA" if encoding_flag else "INTEL"

                            cls.signal[nom_signal] = {
                                'length': longueur,
                                'encoding': encoding,
                                'factor': factor,
                                'offset': offset,
                                'enum': enum_name
                            }
                        else:
                            print(f'[INFO] : APPSIG_Codegen : While in SIGNALS, no signal pattern in line: {line.strip()}')

                    case 'SEND' | 'RECEIVE' | 'SENDRECEIVE':
                        if line.startswith('['):  # Ex: [Symbol1]
                            if waiting_for_timeout  == True and current_read != 'SEND':
                                raise ValueError(f"Missing Timeout for symbol {current_symbol}")

                            current_symbol = line.strip().strip('[]')
                            cls.symbol[current_symbol] = {
                                'msg_id': None,
                                'msg_len': None,
                                'msg_type': None,
                                'msg_direction': current_read,
                                'signals': {},
                                'timeout': 0,
                                'cycle_time': None  # <-- Ajouté ici
                            }
                            waiting_for_timeout = True
                            continue

                        match_id = PATTERN_SYM_ID.match(line)
                        if match_id:
                            current_id = match_id.group(1)
                            current_type = match_id.group(2)

                            if current_type not in cls.list_id:
                                cls.list_id[current_type] = []

                            if current_id in cls.list_id[current_type]:
                                raise ValueError(f'{current_id} already used in msg type {current_type}')
                            else:
                                cls.list_id[current_type].append(current_id)

                            if current_symbol:
                                cls.symbol[current_symbol]['msg_id'] = current_id
                                cls.symbol[current_symbol]['msg_type'] = current_type
                            continue

                        match_len = PATTERN_SYM_LEN.match(line)
                        if match_len:
                            current_len = int(match_len.group(1))
                            if current_symbol:
                                cls.symbol[current_symbol]['msg_len'] = current_len
                            continue

                        # Nouveau bloc : Timeout
                        if line.strip().lower().startswith("timeout="):
                            timeout_val = int(line.strip().split("=")[1].strip())
                            if current_symbol:
                                if timeout_val == 0:
                                    raise ValueError(f"Timeout cannot be 0 for symbol '{current_symbol}'")
                                cls.symbol[current_symbol]['timeout'] = timeout_val
                                waiting_for_timeout = False
                            continue

                        # Nouveau bloc : CycleTime
                        if line.strip().lower().startswith("cycletime="):
                            cycle_val = int(line.strip().split("=")[1].strip())
                            if current_symbol and (current_read == 'SEND' or current_read == 'SENDRECEIVE') :
                                if cycle_val == 0:
                                    raise ValueError(f"CycleTime cannot be 0 for symbol '{current_symbol}'")
                                cls.symbol[current_symbol]['cycle_time'] = cycle_val
                            continue

                        # Ligne signal
                        match_sig = PATTERN_SYM_SIG.match(line)
                        if match_sig:
                            signal_name = match_sig.group(1)
                            position = int(match_sig.group(2))

                            if current_symbol:
                                # Vérifier si le signal est bien défini
                                if signal_name not in cls.signal:
                                    raise ValueError(f"Signal '{signal_name}' utilisé par '{current_symbol}' non défini dans SIGNALS")

                                new_start = position
                                new_length = cls.signal[signal_name]['length']

                                for existing_signal, existing_start in cls.symbol[current_symbol]['signals'].items():
                                    existing_length = cls.signal[existing_signal]['length']

                                    new_end = new_start + new_length - 1
                                    existing_end = existing_start + existing_length - 1

                                    if not (new_end < existing_start or existing_end < new_start):
                                        raise ValueError(
                                            f"Conflit dans '{current_symbol}': signal '{signal_name}' (bits {new_start}-{new_end}) "
                                            f"chevauche '{existing_signal}' (bits {existing_start}-{existing_end})"
                                        )

                                # Pas de conflit, on ajoute le signal
                                cls.symbol[current_symbol]['signals'][signal_name] = position

                            continue

            if current_symbol:
                sym = cls.symbol[current_symbol]
                if sym['msg_direction'] == 'RECEIVE' or sym['msg_direction'] == 'SENDRECEIVE':
                    if sym['timeout'] is None:
                        raise ValueError(f"Missing Timeout for last symbol '{current_symbol}'")
                if sym['msg_direction'] == 'SEND' or sym['msg_direction'] == 'SENDRECEIVE':
                    if sym['cycle_time'] is None:
                        raise ValueError(f"Missing CycleTime for last symbol '{current_symbol}'")
        #-----------------------------------------------------------------
        #-----------------------------make all enum-----------------------
        #-----------------------------------------------------------------

        #-----------------------------------------------------------------
        #------------------------make drivers-----------------------------
        #-----------------------------------------------------------------
       
        #-----------------------------------------------------------------
        #------------------------make code gen----------------------------
        #-----------------------------------------------------------------
        
        
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

