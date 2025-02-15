#!/usr/bin/env python3
import os
import sys
import shutil
import glob
from config import AUTOTASKER_TEMPLATES_PATH
from geom_tools.geom_extract import extract_final_optimized_coordinates_from_log

def ensure_sub_dir():
    """确保 ~/.sub 目录存在，并创建 tasker_add 文件（如果不存在）"""
    sub_dir = os.path.expanduser("~/.sub")
    os.makedirs(sub_dir, exist_ok=True)
    tasker_add = os.path.join(sub_dir, "tasker_add")
    if not os.path.exists(tasker_add):
        open(tasker_add, 'w').close()
    return tasker_add

def add_current_dir_to_tasker():
    """将当前目录添加到 tasker_add 文件"""
    current_dir = os.path.abspath(os.getcwd())
    tasker_add = ensure_sub_dir()
    with open(tasker_add, 'a') as f:
        f.write(f"{current_dir}\n")

def process_log_file(log_file):
    """处理 log 文件，提取信息并生成 com 文件"""
    try:
        # 提取信息
        info = extract_final_optimized_coordinates_from_log(log_file)
        
        # 生成 com 文件名
        base_name = os.path.splitext(os.path.basename(log_file))[0]
        com_file = f"{base_name}.com"
        
        # 写入 com 文件
        with open(com_file, 'w') as f:
            f.write("%chk={}.chk\n".format(base_name))
            if info['keywords']:
                f.write(f"{info['keywords']}\n")
            else:
                f.write("# opt b3lyp/6-31g(d)\n")
            f.write("\nTitle Card Required\n\n")
            f.write(f"{info['charge']} {info['spin_multiplicity']}\n")
            for coord in info['coordinates']:
                f.write(f"{coord}\n")
            f.write("\n")
        
        return com_file
    except Exception as e:
        print(f"Error processing log file {log_file}: {e}")
        return None

def copy_and_process_file(source_file):
    """复制并处理输入文件"""
    try:
        # 获取文件名和扩展名
        base_name = os.path.splitext(os.path.basename(source_file))[0]
        ext = os.path.splitext(source_file)[1].lower()
        
        # 如果源文件在当前目录，直接使用
        if os.path.dirname(os.path.abspath(source_file)) == os.getcwd():
            if ext == '.log':
                return process_log_file(source_file)
            return source_file
            
        # 否则，复制并处理文件
        if ext == '.log':
            shutil.copy2(source_file, '.')
            return process_log_file(os.path.basename(source_file))
        else:
            dest_file = os.path.basename(source_file)
            shutil.copy2(source_file, dest_file)
            return dest_file
    except Exception as e:
        print(f"Error processing file {source_file}: {e}")
        return None

def copy_template_and_rename(input_file, template_name=None):
    """复制模板文件并重命名为与输入文件匹配"""
    try:
        # 确定模板文件路径
        if template_name:
            if not template_name.endswith('.txt'):
                template_name += '.txt'
            template_file = os.path.join(AUTOTASKER_TEMPLATES_PATH, template_name)
        else:
            template_file = os.path.join(AUTOTASKER_TEMPLATES_PATH, "sp.txt")
            
        if not os.path.exists(template_file):
            print(f"Template file not found: {template_file}")
            return False
            
        # 生成新的任务文件名
        base_name = os.path.splitext(input_file)[0]
        task_file = f"{base_name}.task"
        
        # 复制并重命名
        shutil.copy2(template_file, task_file)
        return True
    except Exception as e:
        print(f"Error copying template: {e}")
        return False

def main():
    try:
        template_name = None
        input_file_arg = None
        
        # 解析命令行参数
        if len(sys.argv) > 1:
            if len(sys.argv) > 2:
                # 有两个参数：输入文件和模板名
                input_file_arg = sys.argv[1]
                template_name = sys.argv[2]
            else:
                # 只有一个参数：输入文件
                input_file_arg = sys.argv[1]
        
        if input_file_arg:
            # 处理指定文件
            if not os.path.exists(input_file_arg):
                print(f"Input file not found: {input_file_arg}")
                return 1
                
            # 复制并处理文件
            processed_file = copy_and_process_file(input_file_arg)
            if not processed_file:
                return 1
                
            # 复制并重命名模板
            if not copy_template_and_rename(processed_file, template_name):
                return 1
        else:
            # 无输入文件参数：查找当前目录的 log 文件
            log_files = glob.glob("*.log")
            if not log_files:
                print("No log files found in current directory")
                return 1
                
            # 处理找到的第一个 log 文件
            processed_file = process_log_file(log_files[0])
            if not processed_file:
                return 1
                
            # 复制并重命名模板
            if not copy_template_and_rename(processed_file, template_name):
                return 1
        
        # 将当前目录添加到 tasker_add
        add_current_dir_to_tasker()
        print("Task generation completed successfully")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 