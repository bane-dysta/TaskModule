#!/usr/bin/env python3
import os
import subprocess

def get_unique_dirname(base_name):
    """
    获取唯一的目录名。如果目录已存在，添加数字后缀。
    """
    if not os.path.exists(base_name):
        return base_name
    
    counter = 1
    while os.path.exists(f"{base_name}_{counter}"):
        counter += 1
    return f"{base_name}_{counter}"

def create_test_case():
    """
    创建测试案例目录和文件
    """
    # 获取唯一的目录名
    case_dir = get_unique_dirname("case")
    
    # 创建目录
    os.makedirs(case_dir)
    print(f"Created directory: {case_dir}")
    
    # 创建 methane.com 文件
    com_content = """%chk=methane.chk
# sp

title

0 1
 C                 -3.45755885    0.99736213    0.00000000
 H                 -3.10090442   -0.01144787    0.00000000
 H                 -3.10088601    1.50176032    0.87365150
 H                 -3.10088601    1.50176032   -0.87365150
 H                 -4.52755885    0.99737531    0.00000000"""
    
    com_path = os.path.join(case_dir, "methane.com")
    with open(com_path, "w") as f:
        f.write(com_content)
    print(f"Created file: {com_path}")
    
    # 创建 methane.task 文件
    task_content = "@txt=test"
    
    task_path = os.path.join(case_dir, "methane.task")
    with open(task_path, "w") as f:
        f.write(task_content)
    print(f"Created file: {task_path}")
    
    return case_dir

def run_slurms():
    """
    运行 slurms 命令
    """
    try:
        subprocess.run(["slurms"], check=True)
        print("Successfully ran 'slurms' command")
    except subprocess.CalledProcessError as e:
        print(f"Error running 'slurms' command: {e}")
    except FileNotFoundError:
        print("Error: 'slurms' command not found")

def main():
    """
    主函数
    """
    print("Starting test case generation...")
    case_dir = create_test_case()
    print(f"\nTest case created in directory: {case_dir}")
    
    print("\nRunning slurms command...")
    run_slurms()
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()