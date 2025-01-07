import os
import logging
from commands_words import parse_and_write_commands

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def parse_task_file(task_file):
    """
    解析 .task 文件，仅提取命令词信息。
    只关注任务名称和命令词部分。
    """
    tasks = []
    current_task = {}
    
    with open(task_file, 'r') as f:
        task_content = f.read().split('\n\n')  # 按段落分割
        
        for task in task_content:
            lines = task.strip().split('\n')
            current_task = {
                'job_title': None,
                'command_words': []
            }
            
            for line in lines:
                line = line.strip()
                if line.startswith('$'):  # 匹配任务名称
                    # 去除引号（如果存在）
                    current_task['job_title'] = line.strip('$').strip().strip('"')
                elif line.startswith('!'):  # 处理命令词行
                    command_words = line.strip('!').strip().split()
                    current_task['command_words'] = command_words
            
            # 只有同时有任务名称和命令词的才添加到列表中
            if current_task['job_title'] and current_task['command_words']:
                tasks.append(current_task)
    
    return tasks

def process_task_commands(task_dir):
    """
    处理指定目录下的task文件中的命令词
    """
    logger = setup_logging()
    logger.info(f"Processing task commands in directory: {task_dir}")
    
    try:
        # 查找.task文件
        task_files = [f for f in os.listdir(task_dir) if f.endswith(".task")]
        
        if not task_files:
            logger.info("No .task files found in current directory")
            return
        
        # 处理每个task文件
        for task_file in task_files:
            task_file_path = os.path.join(task_dir, task_file)
            logger.info(f"Processing task file: {task_file}")
            
            # 解析task文件
            tasks = parse_task_file(task_file_path)
            
            # 处理每个任务中的命令词
            for task in tasks:
                if task['command_words']:
                    task_output_dir = os.path.join(task_dir, task['job_title'])
                    
                    # 确保输出目录存在
                    if not os.path.exists(task_output_dir):
                        os.makedirs(task_output_dir)
                    
                    logger.info(f"Processing commands for task: {task['job_title']}")
                    
                    # 解析并写入命令
                    parse_and_write_commands(task['command_words'], task_output_dir)
                    logger.info(f"Commands written for task: {task['job_title']}")
    
    except Exception as e:
        logger.error(f"Error processing task commands: {str(e)}")
        raise

def main():
    """主函数"""
    # 使用当前目录作为任务目录
    current_dir = os.getcwd()
    process_task_commands(current_dir)

if __name__ == "__main__":
    main()