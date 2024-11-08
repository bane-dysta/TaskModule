import os
import re
import subprocess

# 日志文件路径
LOG_FILE_PATH = os.path.expanduser('~/.sub/submit.log')

def parse_submit_log(log_file=LOG_FILE_PATH):
    """
    解析 submit.log 文件，提取任务号和对应的 gjf 文件路径。
    返回一个任务字典，格式为 {'job_id': 'gjf_file_path'}
    """
    tasks = {}

    with open(log_file, 'r') as f:
        for line in f:
            # 使用正则表达式匹配任务号和文件路径
            match = re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} - Job (\d+): (.*\.gjf)$', line)
            if match:
                job_id, gjf_file = match.groups()
                tasks[job_id] = gjf_file
            # 处理任务号为空的情况（即提交失败的情况）
            elif re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} - Job :', line):
                continue

    return tasks

def get_running_jobs():
    """
    使用 squeue 命令获取当前正在运行的任务号。
    返回一个列表，包含当前运行的 job_id。
    """
    running_jobs = []
    try:
        result = subprocess.run(['squeue', '--noheader', '--format=%A'], stdout=subprocess.PIPE, text=True)
        if result.returncode == 0:
            # 按行分割输出，提取 job_id 列表
            running_jobs = result.stdout.strip().split('\n')
        else:
            print("Error executing squeue.")
    except Exception as e:
        print(f"Error running squeue: {e}")

    return running_jobs

def check_job_status(log_file=LOG_FILE_PATH):
    """
    比对 submit.log 和当前运行的任务，返回一个字典。
    字典的格式为 {'job_id': 'running/finished'}，表示每个任务的运行状态。
    """
    job_status = {}
    
    # 解析日志文件中的任务号
    submitted_jobs = parse_submit_log(log_file)
    
    # 获取当前正在运行的任务号
    running_jobs = get_running_jobs()
    
    # 判断每个任务是否还在运行
    for job_id, gjf_file in submitted_jobs.items():
        if job_id in running_jobs:
            job_status[job_id] = 'running'
        else:
            job_status[job_id] = 'finished'

    return job_status

# 测试函数调用
if __name__ == "__main__":
    job_status = check_job_status()
    for job_id, status in job_status.items():
        print(f"Job {job_id}: {status}")
