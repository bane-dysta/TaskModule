# -*- coding: utf-8 -*-
import re
import os

# 原子序号到元素符号的映射
atomic_number_to_symbol = {
    '1': 'H', '2': 'He', '3': 'Li', '4': 'Be', '5': 'B', '6': 'C', '7': 'N', '8': 'O', '9': 'F', '10': 'Ne',
    '11': 'Na', '12': 'Mg', '13': 'Al', '14': 'Si', '15': 'P', '16': 'S', '17': 'Cl', '18': 'Ar', '19': 'K', '20': 'Ca',
    # 添加其他原子序号到元素符号的映射
    '21': 'Sc', '22': 'Ti', '23': 'V', '24': 'Cr', '25': 'Mn', '26': 'Fe', '27': 'Co', '28': 'Ni', '29': 'Cu', '30': 'Zn',
    '31': 'Ga', '32': 'Ge', '33': 'As', '34': 'Se', '35': 'Br', '36': 'Kr', '37': 'Rb', '38': 'Sr', '39': 'Y', '40': 'Zr',
    '41': 'Nb', '42': 'Mo', '43': 'Tc', '44': 'Ru', '45': 'Rh', '46': 'Pd', '47': 'Ag', '48': 'Cd', '49': 'In', '50': 'Sn',
    '51': 'Sb', '52': 'Te', '53': 'I', '54': 'Xe', '55': 'Cs', '56': 'Ba', '57': 'La', '58': 'Ce', '59': 'Pr', '60': 'Nd',
    '61': 'Pm', '62': 'Sm', '63': 'Eu', '64': 'Gd', '65': 'Tb', '66': 'Dy', '67': 'Ho', '68': 'Er', '69': 'Tm', '70': 'Yb',
    '71': 'Lu', '72': 'Hf', '73': 'Ta', '74': 'W', '75': 'Re', '76': 'Os', '77': 'Ir', '78': 'Pt', '79': 'Au', '80': 'Hg',
    '81': 'Tl', '82': 'Pb', '83': 'Bi', '84': 'Po', '85': 'At', '86': 'Rn', '87': 'Fr', '88': 'Ra', '89': 'Ac', '90': 'Th',
    '91': 'Pa', '92': 'U', '93': 'Np', '94': 'Pu', '95': 'Am', '96': 'Cm', '97': 'Bk', '98': 'Cf', '99': 'Es', '100': 'Fm',
    '101': 'Md', '102': 'No', '103': 'Lr', '104': 'Rf', '105': 'Db', '106': 'Sg', '107': 'Bh', '108': 'Hs', '109': 'Mt',
    '110': 'Ds', '111': 'Rg', '112': 'Cn', '113': 'Nh', '114': 'Fl', '115': 'Mc', '116': 'Lv', '117': 'Ts', '118': 'Og'
}

def extract_info_from_gfj(gfj_file_path):
    result = {
        'charge': None,
        'spin_multiplicity': None,
        'coordinates': []
    }

    with open(gfj_file_path, 'r') as file:
        lines = file.readlines()
        start_reading = False
        for line in lines:
            # 跳过以 Lp 开头的行
            if line.startswith("Lp"):
                continue
            if start_reading:
                if line.strip() == '':
                    break
                parts = line.strip().split()

                # 判断该行是否包含元素符号和坐标信息
                if len(parts) == 4:
                    # 常规四部分格式：元素符号 + x + y + z
                    element = parts[0]
                    x = parts[1]
                    y = parts[2]
                    z = parts[3]
                    result['coordinates'].append("{} {} {} {}".format(element, x, y, z))
                elif len(parts) == 5:
                    # 五部分格式：元素符号 + 标记 + x + y + z (跳过标记)
                    element = parts[0]
                    x = parts[2]
                    y = parts[3]
                    z = parts[4]
                    result['coordinates'].append("{} {} {} {}".format(element, x, y, z))
                else:
                    # 忽略不符合格式的行
                    continue
                
            # 识别电荷和自旋多重度的部分，类似于原来的代码
            elif re.match(r'^\s*\d+\s+\d+', line):
                charge_spin = line.strip().split()
                result['charge'] = int(charge_spin[0])
                result['spin_multiplicity'] = int(charge_spin[1])
                start_reading = True
    
    return result

def extract_final_optimized_coordinates_from_log(log_file_path):
    result = {
        'charge': None,
        'spin_multiplicity': None,
        'coordinates': [],
        'keywords': ''
    }

    with open(log_file_path, 'r') as file:
        lines = file.readlines()

    # 从上往下搜索包含 # 的行，获取计算关键词
    # 拼接所有的关键词行
    keywords = []
    collecting_keywords = False
    for line in lines:
        if line.strip().startswith('#'):
            collecting_keywords = True
            keywords.append(line.strip())
        elif collecting_keywords:
            # 遇到以 `----` 开头的行终止关键词提取
            if line.strip().startswith('----'):
                break
            # 继续收集从属行
            elif line.strip():
                # 将当前行与上一行紧密连接，避免引入不必要的空格
                keywords[-1] = keywords[-1] + line.strip()

    # 将拼接后的关键词行保存为结果
    result['keywords'] = ' '.join(keywords)


    standard_orientation_found = False

    # 从后往前遍历，寻找最后一个 "Standard orientation"
    for i in range(len(lines) - 1, -1, -1):
        if 'Standard orientation' in lines[i]:
            standard_orientation_found = True
            j = i + 5  # 坐标数据通常在 "Standard orientation" 行的第五行开始
            while j < len(lines) and '----' not in lines[j]:
                parts = lines[j].strip().split()
                if len(parts) >= 6:
                    atomic_number = parts[1]
                    element = atomic_number_to_symbol.get(atomic_number, atomic_number)
                    x = parts[3]
                    y = parts[4]
                    z = parts[5]
                    result['coordinates'].append("{} {} {} {}".format(element, x, y, z))
                j += 1
            break

    if not standard_orientation_found:
        print("Warning: 'Standard orientation' not found. Using 'Input orientation' coordinates.")
        for i in range(len(lines) - 1, -1, -1):
            if 'Input orientation' in lines[i]:
                j = i + 5  # 坐标数据通常在 "Input orientation" 行的第五行开始
                while j < len(lines) and '----' not in lines[j]:
                    parts = lines[j].strip().split()
                    if len(parts) >= 6:
                        atomic_number = parts[1]
                        element = atomic_number_to_symbol.get(atomic_number, atomic_number)
                        x = parts[3]
                        y = parts[4]
                        z = parts[5]
                        result['coordinates'].append("{} {} {} {}".format(element, x, y, z))
                    j += 1
                break
    
    # 从前往后遍历，寻找 "Charge =  m Multiplicity = n"
    for line in lines:
        match = re.search(r'Charge\s*=\s*(-?\d+)\s+Multiplicity\s*=\s*(\d+)', line)
        if match:
            result['charge'] = int(match.group(1))
            result['spin_multiplicity'] = int(match.group(2))
            break

    return result


def extract_scan_coordinates_from_scan(scan_file_path):
    results = []
    with open(scan_file_path, 'r') as file:
        lines = file.readlines()

    index = 0
    stationary_point_index = 1
    while index < len(lines):
        if 'Stationary point found' in lines[index]:
            # 向上查找 "Input orientation"
            input_orientation_found = False
            for i in range(index, -1, -1):
                if 'Input orientation' in lines[i]:
                    print("Found 'Input orientation' at line:", i)  # 调试信息
                    # 提取坐标数据
                    result = {
                        'index': stationary_point_index,
                        'charge': None,
                        'spin_multiplicity': None,
                        'coordinates': []
                    }
                    j = i + 5  # 坐标数据通常在 "Input orientation" 行的第五行开始
                    while j < len(lines) and '----' not in lines[j]:
                        parts = lines[j].strip().split()
                        if len(parts) >= 6:
                            atomic_number = parts[1]
                            element = atomic_number_to_symbol.get(atomic_number, atomic_number)
                            x = parts[3]
                            y = parts[4]
                            z = parts[5]
                            result['coordinates'].append("{} {} {} {}".format(element, x, y, z))
                        j += 1
                    # 提取电荷和自旋多重度
                    for k in range(i, -1, -1):
                        match = re.search(r'Charge\s*=\s*(-?\d+)\s+Multiplicity\s*=\s*(\d+)', lines[k])
                        if match:
                            result['charge'] = int(match.group(1))
                            result['spin_multiplicity'] = int(match.group(2))
                            break
                    input_orientation_found = True
                    results.append(result)
                    stationary_point_index += 1
                    break
            if not input_orientation_found:
                print("Error: 'Input orientation' not found for 'Stationary point found' at line:", index)
        index += 1

    # 将结果写入临时文件
    with open('scan_results.txt', 'w') as outfile:
        for result in results:
            outfile.write("Stationary Point Index: {}\n".format(result['index']))
            outfile.write("Coordinates:\n")
            for coord in result['coordinates']:
                outfile.write(coord + '\n')
            outfile.write("\n")

    return results

def extract_info_from_xyz(xyz_file_path):
    """
    从 XYZ 文件中提取几何信息、电荷和自旋多重度
    XYZ 格式:
    原子数
    charge spin_multiplicity
    元素符号 x y z
    ...
    """
    result = {
        'charge': None,
        'spin_multiplicity': None,
        'coordinates': []
    }

    with open(xyz_file_path, 'r') as file:
        lines = file.readlines()
        
        # 确保文件至少有3行
        if len(lines) < 3:
            raise ValueError("Invalid XYZ file format: file too short")
            
        # 第二行包含电荷和自旋多重度
        charge_spin = lines[1].strip().split()
        if len(charge_spin) == 2:
            result['charge'] = int(charge_spin[0])
            result['spin_multiplicity'] = int(charge_spin[1])
        
        # 从第三行开始读取坐标
        for line in lines[2:]:
            parts = line.strip().split()
            if len(parts) == 4:  # 元素符号 + x y z
                result['coordinates'].append(line.strip())

    return result

def extract_info_from_input(input_file):
    """
    根据文件扩展名选择合适的提取函数
    """
    ext = os.path.splitext(input_file)[1].lower()
    if ext == '.xyz':
        return extract_info_from_xyz(input_file)
    elif ext in ['.gjf', '.com']:
        return extract_info_from_gfj(input_file)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
