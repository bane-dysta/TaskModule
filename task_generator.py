import os
import re
import logging
from typing import Optional, Tuple

def find_template_file(template_name: str, template_path: Optional[str] = None) -> Optional[str]:
    """
    Find template file with proper path expansion
    """
    def expand_path(path: str) -> str:
        """展开路径中的 ~ 和环境变量"""
        expanded = os.path.expanduser(path)  # 展开 ~
        expanded = os.path.expandvars(expanded)  # 展开环境变量
        return os.path.abspath(expanded)  # 转换为绝对路径

    # 如果提供了完整路径
    if template_path:
        full_path = expand_path(template_path)
        if os.path.isfile(full_path):
            return full_path
        logging.error(f"Template file not found at: {full_path}")
        return None

    # 使用环境变量指定的目录
    template_dir = os.getenv('GAUSSIAN_TEMPLATE_DIR', '')
    if not template_dir:
        # 如果环境变量未设置，尝试使用默认路径
        default_path = "~/scripts/tasks/templates"
        logging.debug(f"GAUSSIAN_TEMPLATE_DIR not set, trying default path: {default_path}")
        template_dir = default_path
    
    template_dir = expand_path(template_dir)
    logging.debug(f"Using template directory: {template_dir}")

    # 构建可能的文件路径
    possible_paths = [
        os.path.join(template_dir, template_name),
        os.path.join(template_dir, f"{template_name}.txt"),
        os.path.join(template_dir, template_name.replace('.txt', ''))
    ]

    # 尝试所有可能的路径
    for path in possible_paths:
        full_path = expand_path(path)
        if os.path.isfile(full_path):
            logging.debug(f"Found template file at: {full_path}")
            return full_path

    # 如果都没找到，记录错误
    logging.error(f"Template file not found. Searched in:\n" + 
                 "\n".join(f"- {expand_path(p)}" for p in possible_paths))
    return None

def parse_txt_directive(line: str) -> Optional[Tuple[str, Optional[str]]]:
    """
    Parse @txt directive to extract filename and optional path.
    Simplified format: @txt=path_or_filename
    """
    txt_pattern = r'@txt=(.+)'
    match = re.match(txt_pattern, line.strip())
    
    if not match:
        return None
        
    file_spec = match.group(1).strip()
    
    # Check if it's a full path or just filename
    if os.path.sep in file_spec:
        directory = os.path.dirname(file_spec)
        filename = os.path.basename(file_spec)
        return filename, directory
    else:
        return file_spec, None

def process_task_file(task_file_path: str) -> bool:
    """
    Process a task file with proper path handling
    """
    try:
        task_file_path = os.path.expanduser(task_file_path)
        with open(task_file_path, 'r') as f:
            content = f.read().strip()
            
        if not content.startswith('@txt=') or content.count('\n') > 0:
            return True
            
        parsed = parse_txt_directive(content)
        if not parsed:
            logging.error(f"Invalid @txt directive in {task_file_path}: {content}")
            return False
            
        filename, specific_path = parsed
        if specific_path:
            specific_path = os.path.expanduser(specific_path)
            
        template_path = find_template_file(
            template_name=filename,
            template_path=os.path.join(specific_path, filename) if specific_path else None
        )
        
        if not template_path:
            return False
            
        # 读取并验证模板内容
        try:
            with open(template_path, 'r') as f:
                template_content = f.read()
                if not template_content.strip():
                    logging.error(f"Template file is empty: {template_path}")
                    return False
            
            # 写回任务文件
            with open(task_file_path, 'w') as f:
                f.write(template_content)
                
            logging.info(f"Successfully imported template from {template_path} to {task_file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error reading/writing template file {template_path}: {str(e)}")
            return False
            
    except Exception as e:
        logging.error(f"Error processing task file {task_file_path}: {str(e)}")
        return False

def check_and_expand_task_file(task_file_path: str) -> bool:
    """
    Main entry point for checking and expanding task files.
    """
    if not os.path.isfile(task_file_path):
        logging.error(f"Task file not found: {task_file_path}")
        return False
        
    try:
        return process_task_file(task_file_path)
    except Exception as e:
        logging.error(f"Unexpected error processing {task_file_path}: {str(e)}")
        return False