#!/usr/bin/env python3
import os
import sys
import logging
from commands_words import parse_and_write_commands

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def process_commands(command_str):
    """
    处理命令字符串，生成comd文件
    
    Args:
        command_str: 命令字符串，格式如 "scripts=(fchk) copy=(*.fchk>../FCclasses)"
    """
    logger = setup_logging()
    current_dir = os.getcwd()
    
    try:
        # 将命令字符串分割成命令词列表
        commands = command_str.strip().split()
        
        # 确保有命令要处理
        if not commands:
            logger.error("No commands provided")
            return False
            
        logger.info(f"Processing commands in directory: {current_dir}")
        
        # 解析并写入命令
        parse_and_write_commands(commands, current_dir)
        logger.info("Commands written to comd file")
        return True
        
    except Exception as e:
        logger.error(f"Error processing commands: {str(e)}")
        return False

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("Usage: python comd.py \"command_string\"")
        print("Example: python comd.py \"scripts=(fchk) copy=(*.fchk>../FCclasses)\"")
        sys.exit(1)
        
    command_str = sys.argv[1]
    if not process_commands(command_str):
        sys.exit(1)

if __name__ == "__main__":
    main() 