import re
from collections import defaultdict

CPU_STM32_XYY_H_FILE = r"C:\Users\mbarb\.platformio\packages\framework-stm32cubeh7\Drivers\CMSIS\Device\ST\STM32H7xx\Include\stm32h753xx.h"
HAL_RCC_H_FILE = r"C:\Users\mbarb\.platformio\packages\framework-stm32cubeh7\Drivers\STM32H7xx_HAL_Driver\Inc\stm32h7xx_hal_rcc.h"

# Exemple d'utilisation
filename = r"C:\Users\mbarb\.platformio\packages\framework-stm32cubeh7\Drivers\CMSIS\Device\ST\STM32H7xx\Include\stm32h753xx.h"
base_list = [
    "D2_APB1PERIPH_BASE",
    "D2_APB2PERIPH_BASE",
    "D2_AHB1PERIPH_BASE",
    "D2_AHB2PERIPH_BASE",
    "D1_APB1PERIPH_BASE",
    "D1_AHB1PERIPH_BASE",
    "D3_APB1PERIPH_BASE",
    "D3_AHB1PERIPH_BASE",
]

base_list_to_bus = {
    "D2_APB1PERIPH_BASE" : "APB1",
    "D2_APB2PERIPH_BASE" : "APB2",
    "D2_AHB1PERIPH_BASE" : "AHB1",
    "D2_AHB2PERIPH_BASE" : "AHB2",
    "D1_APB1PERIPH_BASE" : "APB3",
    "D1_AHB1PERIPH_BASE" : "AHB3",
    "D3_APB1PERIPH_BASE" : "APB4",
    "D3_AHB1PERIPH_BASE" : "AHB4",
}

def extract_rcc_peripherals(rcc_filepath, known_peripherals):
    with open(rcc_filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Trouve toutes les occurences de __HAL_RCC_<Periph>_CLK_ENABLE
    clk_enable_pattern = re.compile(r'#define\s+__HAL_RCC_([A-Za-z0-9_]+)_CLK_ENABLE\s*\(\)\s*(do\s*{[^}]*}|[^\n]+)')

    # Cherche tous les #if defined ou #ifdef <Periph>
    ifdef_pattern = re.compile(r'#\s*(if defined|ifdef)\s*\(?\s*([A-Za-z0-9_]+)\s*\)?')

    conditional_peripherals = set(m.group(2) for m in ifdef_pattern.finditer(content))

    # Dictionnaire : clé = registre RCC (ex: AHB4ENR, AHB1LPENR), valeur = liste des périphériques
    rcc_dict = defaultdict(list)

    for match in clk_enable_pattern.finditer(content):
        periph = match.group(1)
        macro_body = match.group(2)

        # Filtrage comme avant
        if '_IS' in periph or 'C1_' in periph or 'C2_' in periph:
            continue

        # Gestion conditionnel
        if periph in conditional_peripherals and periph not in known_peripherals:
            print(f"Unknown peripheral conditionally defined, skipping: {periph}")
            continue

        # Recherche du registre RCC dans la macro
        # On cherche un pattern RCC-> suivi du registre (par ex AHB4ENR, AHB1LPENR...)
        reg_match = re.search(r'RCC->([A-Za-z0-9_]+)', macro_body)
        if reg_match:
            reg = reg_match.group(1)
        else:
            # Pas trouvé => on peut mettre None ou 'Unknown'
            reg = 'Unknown'

        rcc_dict[reg].append(periph)

    # Convertir en dict classique si besoin (pas obligatoire)
    return dict(rcc_dict)

def classify_peripherals_by_base(filename, base_list):
    peripherals_dict = defaultdict(list)
    periph_list = []
    base_set = set(base_list)

    # Regex adaptée pour gérer : NOM[_R]_BASE
    pattern = re.compile(
        r"#define\s+(\w+?)_BASE\s*\(\s*(\w+)\s*\+\s*0x[0-9A-Fa-f]+UL\s*\)"
    )

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.match(line)
            if match:
                peripheral = match.group(1)  # ex: FLASH_R, FMC_R, DMA1, ...
                base = match.group(2)        # ex: D1_AHB1PERIPH_BASE
                if base in base_set:
                    peripherals_dict[base].append(peripheral)
                    periph_list.append(peripheral)

    return dict(peripherals_dict), periph_list

def extract_peripherals_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extraire la section entre les deux balises
    pattern_section = re.compile(
        r'/\*\*\s*@addtogroup\s+Peripheral_declaration(.*?)'
        r'/\*\*\s*@addtogroup\s+Exported_constants',
        re.DOTALL | re.MULTILINE
    )
    match_section = pattern_section.search(content)
    if not match_section:
        print("Section entre balises non trouvée.")
        return []

    section = match_section.group(1)

    # Regex adaptée pour matcher tous les defines périphériques de cette forme
    # Exemple : #define GPIOA               ((GPIO_TypeDef *) GPIOA_BASE)
    #          #define HRTIM1_TIMA         ((HRTIM_Timerx_TypeDef *) HRTIM1_TIMA_BASE)
    #          #define SAI1_Block_A        ((SAI_Block_TypeDef *)SAI1_Block_A_BASE)
    define_pattern = re.compile(
        r'#define\s+(\w+)\s+\(\(\s*[\w_]+_TypeDef\s*\*\s*\)\s*\w+_BASE\s*\)',
        re.MULTILINE
    )

    peripherals = define_pattern.findall(section)

    return peripherals

def write_peripherals_to_file(rcc_clock, output_filename="peripherals_list.txt"):
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write('RCC ->\n')
        for bus, rcc_list in rcc_clock.items():
            if 'LENR' in str(bus) or 'HENR' in str(bus):
                bus_name = bus[:-4]
            else:
                bus_name = bus[:-3]
            for rcc in rcc_list:
                f.write(f"{rcc} {bus_name}\n")


periph_asso, periph_list = classify_peripherals_by_base(CPU_STM32_XYY_H_FILE, base_list)
print(periph_list)
if 'OCTOSPI1' in periph_list:
    raise Exception()
rcc_clock = extract_rcc_peripherals(HAL_RCC_H_FILE, periph_list)
print(rcc_clock)
# result = classify_peripherals_by_base(filename, base_list)
write_peripherals_to_file(rcc_clock, output_filename='Doc\ConfigPrj\PythonTool_CodeGen\Helpers\peripherals_list.txt')
