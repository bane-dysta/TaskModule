import os
import logging
from config import AUTOTASKER_CALC_PATH

# 定义任务路径
TASKS_DIR = AUTOTASKER_CALC_PATH

def find_task_files(base_dir):
    """
    在指定目录下搜索任务文件。
    
    Args:
        base_dir: 要搜索的基础目录
        
    Returns:
        list: 包含 (task_dir, task_file_path) 元组的列表
    """
    task_files = []
    
    try:
        # 遍历基础目录下的所有子目录
        for subdir in os.listdir(base_dir):
            task_dir = os.path.join(base_dir, subdir)
            if not os.path.isdir(task_dir):
                continue
                
            # 在每个子目录中查找 .task 文件
            dir_files = [f for f in os.listdir(task_dir) if f.endswith(".task")]
            if not dir_files:
                logging.info(f"No .task files found in {task_dir}")
                continue
                
            task_file_path = os.path.join(task_dir, dir_files[0])
            task_files.append((task_dir, task_file_path))
            
    except Exception as e:
        logging.error(f"Error searching for task files in {base_dir}: {str(e)}")
        
    return task_files

def find_input_file(task_dir, task_base_name):
    """
    查找与任务文件同名的输入文件。
    
    Args:
        task_dir: 任务目录
        task_base_name: 任务文件基础名（不含扩展名）
        
    Returns:
        str: 找到的输入文件路径，如果未找到则返回 None
    """
    possible_extensions = ['.com', '.gjf', '.xyz']
    
    for ext in possible_extensions:
        possible_file = os.path.join(task_dir, task_base_name + ext)
        if os.path.exists(possible_file):
            return possible_file
            
    return None

if __name__ == "__main__":
    import sys
    
    # 获取命令行参数指定的路径，如果没有则使用默认路径
    search_dir = TASKS_DIR
    if len(sys.argv) > 1:
        custom_path = os.path.abspath(sys.argv[1])
        if os.path.exists(custom_path):
            search_dir = custom_path
            print(f"Using custom path: {search_dir}")
        else:
            print(f"Warning: Custom path {custom_path} does not exist, using default path")
    
    print(f"Searching for tasks in: {search_dir}")
    
    # 搜索任务文件
    found_tasks = find_task_files(search_dir)
    
    # 打印结果
    for task_dir, task_file in found_tasks:
        print(f"Found task file: {task_file}") 