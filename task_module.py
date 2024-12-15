import os
import re
import sys
import logging
import shutil
from task_generator import check_and_expand_task_file
from config import AUTOTASKER_GEOMTOOLS_PATH, AUTOTASKER_CALC_PATH, AUTOTASKER_LOG_PATH, AUTOTASKER_BASE_PATH, AUTOTASKER_TEMPLATES_PATH

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from orca_generator import OrcaInputGenerator

script_path1 = AUTOTASKER_GEOMTOOLS_PATH
script_path2 = AUTOTASKER_BASE_PATH
sys.path.append(script_path1)
sys.path.append(script_path2)
# 定义任务路径
TASKS_DIR = AUTOTASKER_CALC_PATH
ORCA_TEMPLATES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ORCA')

from geom_extract import extract_info_from_gfj, extract_final_optimized_coordinates_from_log, extract_info_from_input
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
log_file_path = AUTOTASKER_LOG_PATH

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
    解析 .task 文件，提取任务信息并解析命令词。支持 ORCA 任务块。
    """
    tasks = []
    current_task = {}
    in_orca_block = False
    orca_content = []

    with open(task_file, 'r') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.rstrip()
        
        if not line:  # 空行标志着新任务块的开始
            if current_task.get('job_title'):
                if orca_content:
                    current_task['orca_block'] = '\n'.join(orca_content)
                    orca_content = []
                tasks.append(current_task)
            current_task = {}
            in_orca_block = False
            continue
            
        if line.startswith('$'):  # 任务名称
            current_task['job_title'] = line.strip('$').strip()
            if line.startswith('$"') and line.endswith('"'):
                current_task['quoted'] = True
            else:
                current_task['quoted'] = False
        elif line == '-orca-':
            in_orca_block = True
            current_task['type'] = 'orca'
        elif in_orca_block:
            if line.startswith('%'):  # 在 ORCA 块中处理源任务
                current_task['source'] = line.strip('%').strip()
            orca_content.append(line)
        else:
            # 现有的 Gaussian 任务解析逻辑
            if line.startswith('%smiles='):
                current_task['smiles'] = line.split('=', 1)[1].strip()
            elif line.startswith('%'):
                current_task['source'] = line.strip('%').strip()
            elif line.startswith('!'):
                current_task['command_words'] = line.strip('!').strip().split()
            elif line.startswith('#'):
                current_task['keywords'] = line[1:]
            elif line.startswith('add ='):
                current_task['extra_keywords'] = line.split('=')[1].strip()

    # 处理最后一个任务
    if current_task.get('job_title'):
        if orca_content:
            current_task['orca_block'] = '\n'.join(orca_content)
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

    # 正则，确保严格匹配任务块名
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
    Generate .gjf file(s) based on task information.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    input_basename = os.path.basename(input_file)
    logging.info(f"Processing {task_info['job_title']}")

    try:
        # 获取几何信息
        if geometry_data:
            geometry = geometry_data['geometry']
            charge = geometry_data['charge']
            spin_multiplicity = geometry_data['spin_multiplicity']
        elif log_data:
            geometry = log_data['coordinates']
            charge = log_data['charge']
            spin_multiplicity = log_data['spin_multiplicity']
        else:
            input_data = extract_info_from_input(input_file)
            geometry = input_data['coordinates']
            charge = input_data['charge']
            spin_multiplicity = input_data['spin_multiplicity']

        # 展开关键词集
        expanded_keywords = expand_keyword_sets(task_info['keywords'])
        logging.info(f"Expanded keywords: {expanded_keywords}")
        
        # 处理关键词映射
        if '{' in task_info['keywords']:
            options = [opt.strip() for opt in re.findall(r'\{([^}]+)\}', task_info['keywords'])[0].split(',')]
        else:
            options = expanded_keywords

        # 为每个展开的关键词生成文件
        for keyword, option in zip(expanded_keywords, options):
            # 确定文件标识符
            keyword_identifier = f"{option}_" if '{' in task_info['keywords'] else ''

            # 生成文件名
            output_basename = f"{keyword_identifier}{task_info['job_title']}_{os.path.splitext(os.path.basename(input_file))[0]}"
            output_gjf = os.path.join(output_dir, f"{output_basename}.gjf")
            chk_path = os.path.join(output_dir, f"{output_basename}.chk")
            
            logging.info(f"Generating file: {os.path.basename(output_gjf)}")
            
            # 写入 gjf 文件
            with open(output_gjf, 'w') as f:
                # 写入 Link 0 命令
                f.write(f"%chk={chk_path}\n")
                
                # 写入计算关键词
                f.write(f"#{keyword}\n\n")
                
                # 写入标题
                f.write(f"{task_info['job_title']}\n\n")
                
                # 写入电荷和自旋多重度
                f.write(f"{charge} {spin_multiplicity}\n")
                
                # 写入几何坐标
                for coord in geometry:
                    f.write(f"{coord}\n")
                
                # 写入额外关键词（如果有）
                if task_info['extra_keywords']:
                    f.write(f"\n{task_info['extra_keywords']}")
                
                # 写入结束空行
                f.write("\n\n")
            
            logging.info(f"Complete: {os.path.basename(output_gjf)} generated")
    
    except Exception as e:
        logging.error(f"Error in create_gjf_from_task: {str(e)}")
        raise

def process_task_folder(task_dir, output_base_dir):
    """
    Process each task folder, parse tasks and generate corresponding gjf files, and handle commands.
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

        # Parse .task file first to check if we need ORCA generator
        tasks = parse_task_file(task_file_path)
        
        # 只在有 ORCA 任务时才创建生成器
        orca_generator = None
        if any(task.get('type') == 'orca' for task in tasks):
            orca_generator = OrcaInputGenerator(ORCA_TEMPLATES_PATH)

        # Find input file with the same base name as the .task file
        task_base_name = os.path.splitext(task_files[0])[0]
        possible_extensions = ['.com', '.gjf', '.xyz']
        input_file = None
        
        # 按优先级顺序查找输入文件
        for ext in possible_extensions:
            possible_file = os.path.join(task_dir, task_base_name + ext)
            if os.path.exists(possible_file):
                input_file = possible_file
                break

        if not input_file:
            logging.error(f"No input file (.com, .gjf, or .xyz) found for {task_file_path}")
            return

        # Get original file name (without path and extension)
        original_file_name = os.path.splitext(os.path.basename(input_file))[0]
        
        logging.info(f"Starting task: {os.path.basename(task_file_path)}")
        
        for task_info in tasks:
            task_output_dir = os.path.join(task_dir, task_info['job_title'])

            # 首先检查是否是已处理过的任务
            if task_info.get('quoted', False):
                logger.skip(f"{task_info['job_title']} already processed.")
                continue

            # 检查任务类型并分别处理
            if task_info.get('type') == 'orca':
                if orca_generator is None:
                    orca_generator = OrcaInputGenerator(ORCA_TEMPLATES_PATH)
                # ORCA 任务处理
                orca_generator.generate_input(task_info, task_dir, task_output_dir)
                update_task_title_with_quotes(task_file_path, task_info)
                continue

            # Gaussian 任务处理
            geometry_data = process_smiles_field(task_info, task_dir)
            if geometry_data:
                create_gjf_from_task(task_info, input_file, task_output_dir, geometry_data=geometry_data)
                update_task_title_with_quotes(task_file_path, task_info)
                logger.skip(f"{task_info['job_title']} is based on SMILES and does not need log file processing.")
                continue

            # 处理 %restart 的逻辑
            if task_info['source'] == "restart":
                log_file = os.path.join(task_output_dir, f"{task_info['job_title']}_{original_file_name}.log")
                if os.path.exists(log_file):
                    log_data = extract_final_optimized_coordinates_from_log(log_file)
                    create_gjf_from_task(task_info, input_file, task_output_dir, log_data=log_data)
                    process_redo(task_info, task_dir, original_file_name)
                else:
                    logging.error(f"Log file {log_file} not found for restart.")
                    continue
            
            # 处理依赖于其他任务的情况
            elif task_info['source'] != "origin":
                # 构建前一个任务的日志文件路径
                prev_task_log = os.path.join(
                    task_dir, 
                    task_info['source'], 
                    f"{task_info['source']}_{original_file_name}.log"
                )

                if not os.path.exists(prev_task_log):
                    logger.skip(f"Previous task log file not found: {prev_task_log}")
                    continue

                if not check_log_file_for_normal_termination(prev_task_log):
                    logger.skip(f"{os.path.basename(prev_task_log)} unfinished.")
                    continue

                log_data = extract_final_optimized_coordinates_from_log(prev_task_log)
                create_gjf_from_task(task_info, input_file, task_output_dir, log_data=log_data)
            
            else:
                create_gjf_from_task(task_info, input_file, task_output_dir)

            update_task_title_with_quotes(task_file_path, task_info)

            if task_info('command_words'):
                logging.info(f"Processing command words for task: {task_info['job_title']}")
                parse_and_write_commands(task_info['command_words'], task_output_dir)

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
    print("----Starting TASKER----")
    print(f"Processing : {TASKS_DIR}")
    
    # 处理所有任务
    process_all_tasks(TASKS_DIR)
    print("----TASKER complete----")