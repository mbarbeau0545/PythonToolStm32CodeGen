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
import sys,os

# Ajoute le dossier parent (ConfigPrj) au PYTHONPATH
current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))  # <- on remonte d'un cran
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PythonToolCfg.APP_PATH import *

import json 
from PyCodeGene import LoadConfig_FromExcel as LCFE

from FMK_CodeGen.FMKCPU_CodeGen     import FMKCPU_CodeGen as FMKCPU
from FMK_CodeGen.FMKTIM_CodeGen     import FMKTIM_CodeGen as FMKTIM
from FMK_CodeGen.FMKIO_CodeGen      import FMKIO_CodeGen as FMKIO
from FMK_CodeGen.FMKCDA_CodeGen     import FMKCDA_CodeGen as FMKCDA
from FMK_CodeGen.FMKCPU_CodeGen     import FMKCPU_CodeGen as FMKCPU
from FMK_CodeGen.FMKSRL_CodeGen     import FMKSRL_CodeGen as FMKSRL
from FMK_CodeGen.FMKHRT_CodeGen     import FMKHRT_CodeGen as FMKHRT
from FMK_CodeGen.FMKFDCAN_CodeGen   import FMKFDCAN_CodeGen as FMKFDCAN

from App_CodeGen.AppSns_CodeGen     import AppSns_CodeGen as APPSNS
from App_CodeGen.AppAct_CodeGen     import AppAct_CodeGen as APPACT
from App_CodeGen.AppSdm_CodeGen     import AppSdm_CodeGen as APPSDM
from App_CodeGen.AppSpm_CodeGen     import AppSpm_CodeGen as APPSPM
from App_CodeGen.AppLgc_CodeGen     import AppLgc_CodeGen as APPLGC
from App_CodeGen.AppSig_CodeGen     import AppSig_CodeGen as APPSIG
from App_CodeGen.AppSys_Codegen     import AppSys_CodeGen as APPSYS
#------------------------------------------------------------------------------
#                                       CONSTANT
#------------------------------------------------------------------------------
# CAUTION : Automatic generated code section: Start #

# CAUTION : Automatic generated code section: End #
#------------------------------------------------------------------------------
#                                       CLASS
#------------------------------------------------------------------------------
class PythonToolArgError(Exception):
    def __init__(self, message):
        super().__init__(message)

#------------------------------------------------------------------------------
#                             FUNCTION IMPLMENTATION
#------------------------------------------------------------------------------
def main()-> None:
    if not len(sys.argv) == 3:
        raise PythonToolArgError(f"Expected two argument : hardware configuration and software.\n Get {len(sys.argv)} instead")
    hardware_cfg_path = str(sys.argv[1])
    software_cfg_path = str(sys.argv[2])

    if not (os.path.isfile(hardware_cfg_path) 
        or  os.path.isfile(software_cfg_path)):
        FileNotFoundError("Expected two argument, hardware configuration and software.")

    if not os.path.isfile(SYM_MSG_CFG):
        FileNotFoundError('Did not found sym file msg configuration. please update path in APPPATH.py for SYM_MSG_CFG variable')
    print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    print('Start Python tool with')
    print(f'\tHardware Confiougration Path -> {hardware_cfg_path}')
    print(f'\tSoftware Confiougration Path -> {software_cfg_path}')
    print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

    FMKCPU.code_generation(hardware_cfg_path)
    FMKTIM.code_generation(hardware_cfg_path)
    FMKHRT.code_generation(hardware_cfg_path)
    FMKCDA.code_genration(hardware_cfg_path)
    FMKSRL.code_genration(hardware_cfg_path)
    FMKFDCAN.code_genration(hardware_cfg_path)
    FMKIO.code_generation(hardware_cfg_path)

    #--- create Json file for Uds Configuration with the version ---# 
    code_gen = LCFE()
    code_gen.load_excel_file(software_cfg_path)
    gnrl_info = code_gen.get_array_from_excel('GeneralInfoSoftware')[1:][0]
    soft_version = str(f'V{gnrl_info[0]}Pr{gnrl_info[1]}')
    soft_udscfg_path = f"Doc\\ConfigPrj\\UdsCfg\\UdsInfo_{soft_version}.json"

    #--- check if the version already exist, if it exists, we erase it, if it doesn't we create it ----#
    APPSYS.code_generation(software_cfg_path, soft_udscfg_path)
    APPSNS.code_generation(software_cfg_path, soft_udscfg_path)
    APPACT.code_generation(software_cfg_path, soft_udscfg_path)
    APPSDM.code_generation(software_cfg_path, soft_udscfg_path)
    APPSPM.code_generation(software_cfg_path, soft_udscfg_path)
    APPSIG.code_generation(software_cfg_path, SYM_MSG_CFG)
    APPLGC.code_generation(software_cfg_path, soft_udscfg_path)

    print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    print("<<<<<<<<<<<<<<<<<Successfuly made code generation for project>>>>>>>>>>>>>>>>>")
    print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    return
#------------------------------------------------------------------------------
#			                MAIN
#------------------------------------------------------------------------------
if (__name__ == '__main__'):
    main()

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

