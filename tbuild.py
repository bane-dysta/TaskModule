import argparse
import os

# 默认路径
DEFAULT_PATH = os.path.expanduser("~/AutoCalc/tasks")

def generate_task_file(smiles, compound_name, functional, basis, solvent):
    task_template = f"""$opt
%smiles={smiles}
# opt freq {functional}/{basis} scrf=(solvent={solvent})

$td
%opt
# opt td freq symm=veryloose {functional}/{basis} scrf=(solvent={solvent})

$abs
%opt
# td {functional}/{basis} scrf=(solvent={solvent})
"""
    return task_template

def generate_com_file(smiles, compound_name, functional, basis, solvent):
    # 假设 SMILES 对应的分子电荷为 0，多重度为 1
    charge = 0
    multiplicity = 1
    com_template = f"""%chk={compound_name}.chk
# {functional}/{basis} scrf=(solvent={solvent}) opt freq

Compound Name

{charge} {multiplicity}
{smiles}
"""
    return com_template

def read_and_process_smiles_file(file_path):
    processed_lines = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith('"'):
                # 跳过空行或已经处理过的行
                processed_lines.append(line)
                continue
            parts = line.split()
            if len(parts) != 2:
                raise ValueError(f"Invalid format in the file. Expected 'SMILES compound_name'. Got: {line}")
            smiles, compound_name = parts
            yield smiles, compound_name
            processed_lines.append(f'"{line}"')

    # 更新文件内容
    with open(file_path, 'w') as file:
        file.write('\n'.join(processed_lines))

    # 更新文件内容
    with open(file_path, 'w') as file:
        file.write('\n'.join(processed_lines))

def main():
    parser = argparse.ArgumentParser(description='Generate Gaussian input files.')
    parser.add_argument('-f', '--functional', default='wB97XD', help='Functional to use in the calculation (default: wB97XD)')
    parser.add_argument('-b', '--basis', default='TZVP', help='Basis set to use in the calculation (default: TZVP)')
    parser.add_argument('-scrf', '--solvent', default='water', help='Solvent to use in the SCRF method (default: water)')
    parser.add_argument('-p', '--path', default=DEFAULT_PATH, help='Path to the directory containing the SMILES file (default: ~/AutoCalc/tasks)')
    
    args = parser.parse_args()
    
    file_path = os.path.join(args.path, "smiles.txt")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    for smiles, compound_name in read_and_process_smiles_file(file_path):
        task_content = generate_task_file(smiles, compound_name, args.functional, args.basis, args.solvent)
        com_content = generate_com_file(smiles, compound_name, args.functional, args.basis, args.solvent)
        
        # 创建化合物名称命名的文件夹
        output_dir = os.path.join(args.path, compound_name)
        os.makedirs(output_dir, exist_ok=True)
        
        task_filename = os.path.join(output_dir, f"{compound_name}.task")
        com_filename = os.path.join(output_dir, f"{compound_name}.com")
        
        with open(task_filename, 'w') as task_file:
            task_file.write(task_content)
        
        with open(com_filename, 'w') as com_file:
            com_file.write(com_content)
        
        print(f"Gaussian task file has been generated as '{task_filename}'.")
        print(f"Gaussian input file has been generated as '{com_filename}'.")

if __name__ == "__main__":
    main()