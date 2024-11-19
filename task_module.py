import os
import re
import sys
import logging
import shutil
from task_generator import check_and_expand_task_file  # type: ignore

script_path1 = os.path.expanduser('~/scripts/tasks/geom_tools')
script_path2 = os.path.expanduser('~/scripts/tasks')
sys.path.append(script_path1)
sys.path.append(script_path2)
# 定义任务路径
TASKS_DIR = os.path.expanduser("~/AutoCalc/tasks")

from geom_extract import extract_info_from_gfj, extract_final_optimized_coordinates_from_log  # type: ignore
from commands_words import parse_and_write_commands

# 定义新的日志级别 'skip'，设定为比 'info' 低
SKIP_LEVEL_NUM = 15  # 比 info (20) 低，介于 DEBUG (10) 和 INFO (20) 之间
logging.addLevelName(SKIP_LEVEL_NUM, "SKIP")

# 扩展 logging.Logger 类，添加 skip 方法
def skip(self, message, *args, **kws):
    if self.isEnabledFor(SKIP_LEVEL_NUM):
        self._log(SKIP_LEVEL_NUM, message, args, **kws)

logging.Logger.skip = skip

# 获取 Logger 实例
logger = logging.getLogger(__name__)

# 使用之前的日志路径
log_file_path = os.path.expanduser('~/AutoCalc/tasks/task_processing.log')

# 配置日志，指定输出到日志文件
logging.basicConfig(
    filename=log_file_path,  # 使用原先的日志文件路径
    level=logging.INFO,  # 设置日志级别
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 检查是否有 %smiles= 字段
def process_smiles_field(task_info, task_dir):
    """
    处理 task_info 中的 %smiles= 字段，将 SMILES 解析成 3D 几何结构。
    返回几何信息和分子电荷，用于生成 Gaussian 输入文件。
    """
    smiles = task_info.get('smiles', '')

    # 如果有 SMILES 字符串，处理它
    if smiles:
        compound_name = task_info['job_title']

        # 只有在检测到 SMILES 时才导入 RDKit 库
        try:
            import smiles_parser
            geometry_data = smiles_parser.smiles_to_geometry(smiles)
            logging.info(f"Geometry data generated for SMILES: {compound_name}")
            return geometry_data
        except ImportError:
            logging.error("smiles_parser module not found.")
            raise
        except Exception as e:
            logging.error(f"Failed to process SMILES: {e}")
            raise
    return None
  
def parse_task_file(task_file):
    """
    解析 .task 文件，提取任务信息并解析命令词。支持多个命令词。
    """
    tasks = []
    current_task = {}

    with open(task_file, 'r') as f:
        task_content = f.read().split('\n\n')  # 按段落分割
        
        for task in task_content:
            lines = task.split('\n')
            current_task = {
                'job_title': None,
                'source': None,
                'command_words': [],  # 用于存储多个命令
                'keywords': None,
                'extra_keywords': None,
                'smiles': None,  # 新增字段，用于存储 SMILES 字符串
                'quoted': False  # 新增字段，用于判断任务块是否已加引号
            }
            
            for line in lines:
                line = line.strip()
                if line.startswith('$'):  # 匹配任务名称
                    current_task['job_title'] = line.strip('$').strip()
                    if line.startswith('$"') and line.endswith('"'):  # 检查是否带引号
                        current_task['quoted'] = True
                elif line.startswith('%smiles='):  # 匹配 SMILES 字段
                    current_task['smiles'] = line.split('=', 1)[1].strip()
                    # print("debug_SMILES:", current_task['smiles'])
                elif line.startswith('%'):  # 匹配来源任务
                    current_task['source'] = line.strip('%').strip()
                elif line.startswith('!'):  # 处理命令词行
                    command_words = line.strip('!').strip().split()
                    current_task['command_words'] = command_words
                elif line.startswith('#'):  # 匹配关键词
                    current_task['keywords'] = line[1:]  # 去除 '#'，但保留其余空格
                elif line.startswith('add ='):  # 匹配额外关键词
                    current_task['extra_keywords'] = line.split('=')[1].strip().replace('\\n', '\n')

            # 确保任务有名称，才认为是有效任务
            if current_task['job_title']:
                tasks.append(current_task)

    return tasks

def expand_keyword_sets(keywords):
    """
    Expands keyword sets in the format {a,b,c} to multiple keyword strings.
    """
    pattern = r'\{([^}]+)\}'
    matches = re.findall(pattern, keywords)
    
    if not matches:
        return [keywords]
    
    expanded_keywords = []
    base_keywords = re.sub(pattern, '{}', keywords)
    
    for match in matches:
        options = [option.strip() for option in match.split(',')]
        if not expanded_keywords:
            expanded_keywords = [base_keywords.format(option) for option in options]
        else:
            new_expanded = []
            for existing in expanded_keywords:
                for option in options:
                    new_expanded.append(existing.format(option))
            expanded_keywords = new_expanded
    
    return expanded_keywords
  
def update_task_title_with_quotes(task_file_path, task_info):
    """
    将任务块的标题加引号，并更新到 .task 文件。确保只对匹配的任务块名进行修改。
    """
    with open(task_file_path, 'r') as f:
        lines = f.readlines()

    updated_lines = []
    task_title = f'$"{task_info["job_title"]}"'  # 为任务标题加引号

    # 正则模式，确保严格匹配任务块名
    task_title_pattern = rf'^\${re.escape(task_info["job_title"])}$'

    for line in lines:
        # 确保只修改完全匹配的任务块名称
        if re.match(task_title_pattern, line.strip()):
            updated_lines.append(line.replace(f"${task_info['job_title']}", task_title))
        else:
            updated_lines.append(line)

    # 写回文件
    with open(task_file_path, 'w') as f:
        f.writelines(updated_lines)

def check_log_file_for_normal_termination(log_file):
    """
    检查 .log 文件的最后一行是否包含 'Normal termination' 标记
    """
    if not os.path.exists(log_file):
        logging.warning(f"Log file {log_file} does not exist.")
        return False

    try:
        # 只读取最后一行
        with open(log_file, 'rb') as f:
            f.seek(-2, os.SEEK_END)  # 倒数第二个字节开始向前找换行符
            while f.read(1) != b'\n':  
                f.seek(-2, os.SEEK_CUR)  # 向前移动读取位置直到找到换行符
            last_line = f.readline().decode().strip()
        
        if "Normal termination" in last_line:
            return True
    except Exception as e:
        logging.error(f"Error reading log file {log_file}: {e}")

    return False


def process_redo(task_info, task_dir, original_file_name):
    task_output_dir = os.path.join(task_dir, task_info['job_title'])
    fail_dir = os.path.join(task_output_dir, "fail")

    # 如果 fail 文件夹已经存在，寻找新的 failX 文件夹
    counter = 1
    while os.path.exists(fail_dir):
        fail_dir = os.path.join(task_output_dir, f"fail{counter}")
        counter += 1

    os.makedirs(fail_dir)

    # 移动任务相关的文件到 fail 文件夹，文件名格式为：任务名称_原文件名.ext
    files_to_move = ["gjf", "chk", "log"]
    for ext in files_to_move:
        file_path = os.path.join(task_output_dir, f"{task_info['job_title']}_{original_file_name}.{ext}")
        if os.path.exists(file_path):
            shutil.move(file_path, fail_dir)
        else:
            logger.skip(f"redo:{file_path} doesn't exist.")
    
    return True


def create_gjf_from_task(task_info, input_file, output_dir, log_data=None, geometry_data=None):
    """
    Generate .gjf file(s) based on task information. Replace keywords, handle %chk line,
    and expand keyword sets. If geometry_data is provided (e.g., from SMILES), use it.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    input_basename = os.path.basename(input_file)
    
    logging.info(f"Processing {task_info['job_title']}")

    try:
        # 如果提供了几何数据（如 SMILES 解析的结果），使用它
        if geometry_data:
            geometry = geometry_data['geometry']
            charge = geometry_data['charge']
            spin_multiplicity = geometry_data['spin_multiplicity']
        elif log_data:
            geometry = log_data['coordinates']
            charge = log_data['charge']
            spin_multiplicity = log_data['spin_multiplicity']
        else:
            # 如果没有提供几何数据或日志数据，从 input_file 中提取
            gjf_data = extract_info_from_gfj(input_file)
            geometry = gjf_data['coordinates']
            charge = gjf_data['charge']
            spin_multiplicity = gjf_data['spin_multiplicity']
        
        with open(input_file, 'r') as f:
            file_content = f.readlines()

        # Remove trailing empty lines
        while file_content and file_content[-1].strip() == '':
            file_content.pop()

        # Expand keyword sets
        expanded_keywords = expand_keyword_sets(task_info['keywords'])
        logging.info(f"Expanded keywords: {expanded_keywords}")
        
        # Get set content for mapping keywords to file names
        set_content = None
        if '{' in task_info['keywords']:
            set_content = re.findall(r'\{([^}]+)\}', task_info['keywords'])[0]
            options = [opt.strip() for opt in set_content.split(',')]
        else:
            options = expanded_keywords
        
        # Map each expanded keyword to the corresponding set element, or skip if no braces are present
        for keyword, option in zip(expanded_keywords, options):
            # 判断关键词是否包含花括号
            if '{' in task_info['keywords']:
                keyword_identifier = f"{option}_"  # Use the element from the set as the identifier
            else:
                keyword_identifier = ''  # 如果不包含花括号，忽略该部分

            # 生成 .gjf 和 .chk 文件的名称
            output_gjf_name = f"{keyword_identifier}{task_info['job_title']}_{os.path.splitext(os.path.basename(input_file))[0]}.gjf"
            output_gjf = os.path.join(output_dir, output_gjf_name)
            new_chk_path = os.path.join(output_dir, f"{keyword_identifier}{task_info['job_title']}_{os.path.splitext(os.path.basename(input_file))[0]}.chk")
            
            logging.info(f"Generating file: {output_gjf_name}")
            
            file_lines_without_geometry = []
            in_geometry_section = False
            chk_line_present = False

            for line in file_content:
                if line.startswith("%chk"):
                    chk_line_present = True
                    file_lines_without_geometry.append(f"%chk={new_chk_path}\n")
                elif line.startswith("#"):
                    file_lines_without_geometry.append(f"#{keyword}\n")
                elif re.match(r'^\s*\d+\s+\d+', line):
                    file_lines_without_geometry.append(f"{charge} {spin_multiplicity}")
                    in_geometry_section = True
                elif in_geometry_section and line.strip() == '':
                    in_geometry_section = False
                elif not in_geometry_section:
                    file_lines_without_geometry.append(line)

            if not chk_line_present:
                file_lines_without_geometry.insert(0, f"%chk={new_chk_path}\n")

            with open(output_gjf, 'w') as f_out:
                for line in file_lines_without_geometry:
                    f_out.write(line)
                
                # 如果有几何数据，则将几何信息写入
                if geometry:
                    f_out.write("\n")
                    for geo_line in geometry:
                        f_out.write(geo_line + "\n")
                
                # 如果有额外的关键字
                if task_info['extra_keywords']:
                    f_out.write(f"{task_info['extra_keywords']}\n")
                
                f_out.write("\n\n")
            
            logging.info(f"Complete: {os.path.basename(output_gjf)} generated")
    
    except Exception as e:
        logging.error(f"Error in create_gjf_from_task: {str(e)}")
        raise

def process_task_folder(task_dir, output_base_dir):
    """
    Process each task folder, parse tasks and generate corresponding gjf files, and handle commands.
    If a task block is already quoted, only execute commands without generating gjf files.
    """
    try:
        # Find .task files
        task_files = [f for f in os.listdir(task_dir) if f.endswith(".task")]
        
        if not task_files:
            logging.info(f"No .task files found in {task_dir}")
            return
        
        task_file_path = os.path.join(task_dir, task_files[0])

        if not check_and_expand_task_file(task_file_path):
            logging.error(f"Failed to process task template in {task_file_path}")
            return

        # Find .com or .gjf file with the same name as the .task file
        com_file_path = task_file_path.replace(".task", ".com")
        gjf_file_path = task_file_path.replace(".task", ".gjf")

        # Prioritize .com file, use .gjf if .com doesn't exist
        if os.path.exists(com_file_path):
            input_file = com_file_path
        elif os.path.exists(gjf_file_path):
            input_file = gjf_file_path
        else:
            logging.info(f"No .com or .gjf files found for {task_file_path}")
            return

        # Get original file name (without path and extension)
        original_file_name = os.path.basename(input_file).replace('.com', '').replace('.gjf', '')

        # Parse .task file
        tasks = parse_task_file(task_file_path)
        
        # Log the start of processing the .task file
        logging.info(f"Starting task: {os.path.basename(task_file_path)}")
        
        # Process each task to generate new .gjf files or handle commands
        for task_info in tasks:
            task_output_dir = os.path.join(task_dir, task_info['job_title'])

            # 如果任务块已经加引号，表示已经处理完，则跳过
            if task_info['quoted']:
                logger.skip(f"{task_info['job_title']} already processed.")
                continue
                
            # 优先处理 SMILES 字段，如果检测到 %smiles= 字段，直接处理几何生成
            geometry_data = process_smiles_field(task_info, task_dir)
            if geometry_data:
                # 如果有 SMILES 几何数据，将其传递给 create_gjf_from_task 并跳过日志检查
                create_gjf_from_task(task_info, input_file, task_output_dir, geometry_data=geometry_data)
                # 打引号，更新任务块
                update_task_title_with_quotes(task_file_path, task_info)
                logger.skip(f"{task_info['job_title']} is based on SMILES and does not need log file processing.")
                continue  # SMILES 已处理，不需要后续处理

            # 处理 %restart 的逻辑
            if task_info['source'] == "restart":
                log_file = os.path.join(task_output_dir, f"{task_info['job_title']}_{original_file_name}.log")
                if os.path.exists(log_file):
                    log_data = extract_final_optimized_coordinates_from_log(log_file)
                    # 生成 .gjf 文件，使用日志中提取的几何数据
                    create_gjf_from_task(task_info, input_file, task_output_dir, log_data=log_data)
                    # 在成功提取几何后，将原始文件移动到 fail 文件夹
                    process_redo(task_info, task_dir, original_file_name)
                else:
                    logging.error(f"Log file {log_file} not found for restart.")
                    continue  # Skip this task if log file doesn't exist
            
            # 处理依赖于其他任务的情况
            elif task_info['source'] != "origin":
                prev_task_log = os.path.join(task_dir, task_info['source'], f"{task_info['source']}_{os.path.basename(input_file).replace('.gjf', '.log').replace('.com', '.log')}")

                if not check_log_file_for_normal_termination(prev_task_log):
                    logger.skip(f"{os.path.basename(prev_task_log)} unfinished.")
                    continue

                # 从之前任务的日志文件中提取几何信息
                log_data = extract_final_optimized_coordinates_from_log(prev_task_log)
                create_gjf_from_task(task_info, input_file, task_output_dir, log_data=log_data)
            
            # 如果任务来源是 origin（初始任务），使用原始几何信息
            else:
                create_gjf_from_task(task_info, input_file, task_output_dir)

            # 为成功生成 .gjf 文件的任务块加引号
            update_task_title_with_quotes(task_file_path, task_info)

            # 处理命令
            if task_info['command_words']:
                logging.info(f"Processing command words for task: {task_info['job_title']}")
                parse_and_write_commands(task_info['command_words'], task_output_dir)

        # Log completion of processing and add a blank line
        logging.info(f"Leaving task: {os.path.basename(task_file_path)}\n")

    except Exception as e:
        logging.error(f"Error processing task folder {task_dir}: {str(e)}")

def process_all_tasks(base_dir):
    """
    遍历所有任务文件夹，逐个处理
    """
    for subdir in os.listdir(base_dir):
        task_dir = os.path.join(base_dir, subdir)
        if os.path.isdir(task_dir):
            process_task_folder(task_dir, task_dir)  # 任务的输出文件夹为当前目录下

if __name__ == "__main__":
    print("Starting the script...")
    print(f"Processing tasks in directory: {TASKS_DIR}")
    
    # 处理所有任务
    process_all_tasks(TASKS_DIR)
    print("Script execution completed.")