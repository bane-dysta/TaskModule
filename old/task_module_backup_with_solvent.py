import os
import re
import sys
import logging
import shutil

script_path = os.path.expanduser('~/apprepo/gaussian/16-hy/scripts/python')
sys.path.append(script_path)

from geom_extract import extract_info_from_gfj, extract_final_optimized_coordinates_from_log # type: ignore

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
    level=logging.DEBUG,  # 设置日志级别
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def parse_solvents(solvents_file):
    """
    解析 solvents.dat 文件，返回一个字典，键为溶剂名称，值为别名（如果有）。
    """
    solvents = {}
    with open(solvents_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("//") or not line:
                continue  # 跳过注释和空行
            if '=' in line:
                solvent, alias = line.split('=', 1)
                solvents[solvent.strip()] = alias.strip()
            else:
                solvents[line] = None  # 无别名
    return solvents

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
                'commands': [],  # 用于存储多个命令
                'keywords': None,
                'extra_keywords': None,
                'quoted': False  # 新增字段，用于判断任务块是否已加引号
            }
            
            for line in lines:
                line = line.strip()
                if line.startswith('$'):  # 匹配任务名称
                    current_task['job_title'] = line.strip('$').strip()
                    if line.startswith('$"') and line.endswith('"'):  # 检查是否带引号
                        current_task['quoted'] = True
                elif line.startswith('%'):  # 匹配来源任务
                    current_task['source'] = line.strip('%').strip()
                elif line.startswith('!'):  # 匹配命令词，支持多个命令
                    commands = line.strip('!').strip().split()
                    current_task['commands'] = commands
                elif line.startswith('#'):  # 匹配关键词
                    current_task['keywords'] = line.strip('#').strip()
                elif line.startswith('add ='):  # 匹配额外关键词
                    current_task['extra_keywords'] = line.split('=')[1].strip().replace('\\n', '\n')

            # 确保任务有名称，才认为是有效任务
            if current_task['job_title']:
                tasks.append(current_task)

    return tasks

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
  
def update_task_file(task_file_path, task_info):
    """
    更新 .task 文件，为已处理的命令添加引号，并确保不会重复执行。
    """
    with open(task_file_path, 'r') as f:
        lines = f.readlines()

    # 对任务文件中每行命令进行更新
    for i, line in enumerate(lines):
        if line.startswith('!'):
            commands = line.strip('!').strip().split()
            quoted_commands = []
            for cmd in commands:
                # 如果命令已经成功执行，给命令添加引号
                if cmd not in task_info['commands'] or (cmd.startswith('"') and cmd.endswith('"')):
                    quoted_commands.append(cmd)  # 保留已经有引号的命令
                else:
                    quoted_commands.append(f'"{cmd}"')
            lines[i] = f"! {' '.join(quoted_commands)}\n"

    with open(task_file_path, 'w') as f:
        f.writelines(lines)
def check_log_file_for_normal_termination(log_file):
    """
    检查 .log 文件是否有 'Normal termination' 标记
    """
    if not os.path.exists(log_file):
        logging.warning(f"Log file {log_file} does not exist.")
        return False

    with open(log_file, 'r') as f:
        lines = f.readlines()
        if any("Normal termination" in line for line in lines):
            return True
    return False

def process_command(task_info, task_dir, original_file_name, task_file_path):
    """
    处理多个命令词。即使某个命令失败，仍然尝试执行剩余的命令。
    为每个命令跟踪成功状态，避免重复执行已经成功的命令。
    """
    command_status = {}  # 用于存储每个命令的执行状态

    logging.info(f"Processing commands for task: {task_info['job_title']}")
    
    for command in task_info['commands']:
        # 如果命令已经被引号引住，则跳过处理
        if command.startswith('"') and command.endswith('"'):
            logger.skip(f"Command:{command}")
            continue

        logging.info(f"Processing command: {command}")

        if command == "redo":
            command_status[command] = process_redo(task_info, task_dir, original_file_name)
        elif command == "fchk":
            command_status[command] = process_fchk(task_info, task_dir, original_file_name)
        elif command == "solvent":
            command_status[command] = process_solvent(task_info, task_dir, original_file_name)
        else:
            logging.warning(f"Unknown command: {command}")
            command_status[command] = False

        # 根据命令的执行结果记录日志
        if command_status[command]:
            logging.info(f"Command {command} executed successfully.")
        else:
            logging.error(f"Command {command} failed for task {task_info['job_title']}.")

    # 更新 .task 文件，为成功的命令添加引号
    update_task_file(task_file_path, task_info)

    # 统计命令执行情况，返回是否全部成功
    all_success = all(command_status.values())
    return all_success

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

def process_fchk(task_info, task_dir, original_file_name):
    task_output_dir = os.path.join(task_dir, task_info['job_title'])
    log_file = os.path.join(task_output_dir, f"{task_info['job_title']}_{original_file_name}.log")
    chk_file = os.path.join(task_output_dir, f"{task_info['job_title']}_{original_file_name}.chk")
    fchk_file = os.path.join(task_output_dir, f"{task_info['job_title']}_{original_file_name}.fchk")

    if not os.path.exists(log_file):
        logging.info(f"Log file {log_file} does not exist.")
        return False

    if not check_log_file_for_normal_termination(log_file):
        logging.info(f"Log file {log_file} has not finished normally.")
        return False

    if os.path.exists(fchk_file):
        return True

    fchk_script = os.path.expanduser("~/apprepo/gaussian/16-hy/scripts/fchk.sh")
    os.system(f"{fchk_script} -r {chk_file}")

    if os.path.exists(fchk_file):
        return True

    return False

def process_solvent(task_info, task_dir, original_file_name):
    """
    处理 solvent 命令：根据不同的溶剂生成对应的 gjf 文件，调用 create_gjf_from_task 统一生成。
    """
    task_output_dir = os.path.join(task_dir, task_info['job_title'])
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solvents_file = os.path.join(script_dir, 'solvents.dat')
    
    if not os.path.exists(solvents_file):
        logging.error(f"Solvents file {solvents_file} does not exist.")
        return False

    solvents = parse_solvents(solvents_file)  # 解析 solvents.dat 文件，得到溶剂列表
    logging.info(f"Parsed solvents: {solvents}")
    
    success = True
    for solvent, alias in solvents.items():
        solvent_name = alias if alias else solvent
        
        # 使用 create_gjf_from_task 生成新的 .gjf 文件，传入溶剂参数
        try:
            create_gjf_from_task(task_info, original_file_name, task_output_dir, log_data=None, solvent=solvent_name)
            logging.info(f"Created solvent file for {solvent_name}.")
        except Exception as e:
            logging.error(f"Error creating solvent file for {solvent_name}: {str(e)}")
            success = False

    return success

def create_gjf_from_task(task_info, input_file, output_dir, log_data=None, solvent=None):
    """
    根据任务信息生成 .gjf 文件。替换关键词，处理 %chk 行，支持溶剂参数。
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    input_basename = os.path.basename(input_file)
    output_gjf_name = f"{task_info['job_title']}_{input_basename.replace('.com', '.gjf')}"
    
    # 如果有溶剂，则在文件名中加入溶剂名称
    if solvent:
        output_gjf_name = f"{solvent}-{output_gjf_name}"
        
    # Add this to debug output file name
    logging.debug(f"Output GJF name: {output_gjf_name}")

    output_gjf = os.path.join(output_dir, output_gjf_name)
    
    chk_basename = input_basename.replace(".gjf", ".chk").replace(".com", ".chk")
    new_chk_path = os.path.join(output_dir, f"{task_info['job_title']}_{chk_basename}")
    
    # Add this to debug the chk path
    logging.debug(f"New chk path: {new_chk_path}")
    
    logging.info(f"Processing {task_info['job_title']}, solvent: {solvent if solvent else 'none'}")
    
    try:
        if log_data:
            geometry = log_data['coordinates']
            charge = log_data['charge']
            spin_multiplicity = log_data['spin_multiplicity']
        else:
            gjf_data = extract_info_from_gfj(input_file)
            geometry = gjf_data['coordinates']
            charge = gjf_data['charge']
            spin_multiplicity = gjf_data['spin_multiplicity']
        
        with open(input_file, 'r') as f:
            file_content = f.readlines()

        # 删除文件末尾多余的空行
        while file_content and file_content[-1].strip() == '':
            file_content.pop()

        file_lines_without_geometry = []
        in_geometry_section = False
        chk_line_present = False  # 用于跟踪 %chk 行是否存在

        for line in file_content:
            # 检查是否有 %chk 行
            if line.startswith("%chk"):
                chk_line_present = True  # 找到 %chk 行
                file_lines_without_geometry.append(f"%chk={new_chk_path}\n")  # 更新 %chk 行
            # 替换关键词行
            elif line.startswith("#"):
                # 用任务的关键词替换当前行
                new_keywords = task_info['keywords']
                # 如果有溶剂参数，则在关键词行后添加 scrf=(solvent=...)
                logging.debug(f"334: {task_info['job_title']}, {task_info['keywords']}, {solvent}")
                if solvent:
                    file_lines_without_geometry.append(f"#{new_keywords} scrf=(solvent={solvent})\n")
                else:
                    file_lines_without_geometry.append(f"#{new_keywords}\n")
            elif re.match(r'^\s*\d+\s+\d+', line):
                # 几何区域：替换电荷和自旋多重度
                file_lines_without_geometry.append(f"{charge} {spin_multiplicity}")
                in_geometry_section = True
            elif in_geometry_section and line.strip() == '':
                in_geometry_section = False
            elif not in_geometry_section:
                file_lines_without_geometry.append(line)

        # 如果没有找到 %chk 行，自动插入一行
        if not chk_line_present:
            file_lines_without_geometry.insert(0, f"%chk={new_chk_path}\n")

        # 生成 .gjf 文件
        with open(output_gjf, 'w') as f_out:
            for line in file_lines_without_geometry:
                f_out.write(line)
            
            if geometry:
                f_out.write("\n")
                for geo_line in geometry:
                    f_out.write(geo_line + "\n")
            
            if task_info['extra_keywords']:
                f_out.write(f"{task_info['extra_keywords']}\n")
            
            f_out.write("\n\n")
        
        logging.info(f"Complete: {os.path.basename(output_gjf)} generated")
    
    except Exception as e:
        logging.error(f"Error: {str(e)}")

def process_task_folder(task_dir, output_base_dir):
    """
    处理每个任务文件夹，解析任务并生成对应的 gjf 文件，并处理命令词。
    如果任务块已经带引号，只执行命令，不再生成 gjf 文件。
    """
    try:
        # 查找 .task 文件
        task_files = [f for f in os.listdir(task_dir) if f.endswith(".task")]
        
        if not task_files:
            logging.info(f"No .task files found in {task_dir}")
            return
        
        task_file_path = os.path.join(task_dir, task_files[0])

        # 查找与 .task 文件同名的 .com 或 .gjf 文件
        com_file_path = task_file_path.replace(".task", ".com")
        gjf_file_path = task_file_path.replace(".task", ".gjf")

        # 优先选择 .com 文件，如果不存在则使用 .gjf 文件
        if os.path.exists(com_file_path):
            input_file = com_file_path
        elif os.path.exists(gjf_file_path):
            input_file = gjf_file_path
        else:
            logging.info(f"No .com or .gjf files found for {task_file_path}")
            return

        # 获取原文件名（去掉路径和扩展名）
        original_file_name = os.path.basename(input_file).replace('.com', '').replace('.gjf', '')

        # 解析 .task 文件
        tasks = parse_task_file(task_file_path)
        
        # 日志记录开始处理 .task 文件
        logging.info(f"Starting task: {os.path.basename(task_file_path)}")
        
        # 对每个任务生成新的 .gjf 文件或处理命令
        for task_info in tasks:
            # 确定输出文件夹为当前 .task 文件目录下的任务名文件夹
            task_output_dir = os.path.join(task_dir, task_info['job_title'])
            output_gjf = os.path.join(task_output_dir, f"{task_info['job_title']}_{os.path.basename(input_file).replace('.com', '.gjf')}")

            # 如果任务块已经带引号，跳过 gjf 文件生成，只处理命令
            if task_info['quoted']:
                logger.skip(f"{task_info['job_title']} done yet.")
                if task_info['commands']:  # 检查是否有命令词
                    process_command(task_info, task_dir, original_file_name, task_file_path)
                continue
                
            # 处理命令词
            if task_info['commands']:
                process_command(task_info, task_dir, original_file_name, task_file_path)

            # 处理 %restart 逻辑
            if task_info['source'] == "restart":
                log_file = os.path.join(task_output_dir, f"{task_info['job_title']}_{original_file_name}.log")
                if os.path.exists(log_file):
                    log_data = extract_final_optimized_coordinates_from_log(log_file)
                    # 提取几何成功后，移动原来的文件到 fail 文件夹
                    process_redo(task_info, task_dir, original_file_name)
                else:
                    logging.error(f"Log file {log_file} not found for restart.")
                    continue  # 如果 log 文件不存在，跳过该任务

            # 处理任务依赖或原始几何信息
            elif task_info['source'] != "origin":
                prev_task_log = os.path.join(task_dir, task_info['source'], f"{task_info['source']}_{os.path.basename(input_file).replace('.gjf', '.log').replace('.com', '.log')}")

                if not check_log_file_for_normal_termination(prev_task_log):
                    logger.skip(f"{os.path.basename(prev_task_log)} unfinished.")
                    continue

                # 从前置任务的 log 文件中提取几何信息
                log_data = extract_final_optimized_coordinates_from_log(prev_task_log)
            else:
                log_data = None  # 对于初始任务，使用原始几何信息

            # 创建输出目录（如果不存在）
            os.makedirs(task_output_dir, exist_ok=True)

            # 根据任务信息生成 gjf 文件
            create_gjf_from_task(task_info, input_file, task_output_dir, log_data)

            # 在生成 gjf 文件后，为任务块标题加引号
            update_task_title_with_quotes(task_file_path, task_info)

        # 日志记录处理完成并添加空行
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

# 定义任务路径
TASKS_DIR = os.path.expanduser("~/AutoCalc/tasks")

if __name__ == "__main__":
    print("Starting the script...")
    print(f"Processing tasks in directory: {TASKS_DIR}")
    
    # 处理所有任务
    process_all_tasks(TASKS_DIR)
    print("Script execution completed.")