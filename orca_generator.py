import os
import re
import sys
import logging
from typing import Dict, Optional, Tuple

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
geom_tools_dir = os.path.join(current_dir, 'geom_tools')
if geom_tools_dir not in sys.path:
    sys.path.append(geom_tools_dir)

from geom_extract import extract_final_optimized_coordinates_from_log

logger = logging.getLogger(__name__)

class OrcaInputGenerator:
    def __init__(self, templates_dir: str):
        """
        初始化 ORCA 输入文件生成器
        
        Args:
            templates_dir: ORCA 模板文件所在目录
        """
        self.templates_dir = templates_dir
        self.templates_cache: Dict[str, Dict] = {}  # 缓存已加载的模板
        
    def _load_template(self, template_name: str) -> Dict:
        """
        加载并解析模板文件
        
        Returns:
            Dict 包含模板内容和默认值
        """
        template_path = os.path.join(self.templates_dir, f"{template_name}.inp")
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")
            
        template_content = []
        defaults = {}
        reading_defaults = False
        
        with open(template_path, 'r') as f:
            for line in f:
                if line.strip() == '-default-':
                    reading_defaults = True
                    continue
                    
                if reading_defaults:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        defaults[key.strip()] = value.strip()
                else:
                    template_content.append(line.rstrip())
        
        return {
            'content': template_content,
            'defaults': defaults
        }
    
    def _parse_control_line(self, control_line: str) -> Dict:
        """
        解析模板控制行
        
        Args:
            control_line: 以 # 开头的控制行
            
        Returns:
            Dict 包含解析后的参数
        """
        params = {}
        # 移除开头的 #
        control_line = control_line.lstrip('#').strip()
        
        # 使用正则表达式匹配 key=value 对
        for match in re.finditer(r'(\w+)=([^\s]+)', control_line):
            key, value = match.groups()
            params[key] = value
            
        return params
    
    def _convert_log_to_xyz(self, log_file: str, output_dir: str) -> Tuple[str, int, int]:
        """
        将 Gaussian log 文件转换为 xyz 格式
        
        Returns:
            Tuple[str, int, int]: (xyz文件路径, 电荷, 自旋多重度)
        """
        # 提取几何信息
        log_data = extract_final_optimized_coordinates_from_log(log_file)
        if not log_data['coordinates']:
            raise ValueError(f"Failed to extract coordinates from {log_file}")
            
        # 构建 xyz 文件路径
        xyz_file = os.path.join(output_dir, 
                               f"{os.path.splitext(os.path.basename(log_file))[0]}.xyz")
        
        # 写入 xyz 文件
        with open(xyz_file, 'w') as f:
            # 第一行：原子数
            f.write(f"{len(log_data['coordinates'])}\n")
            # 第二行：注释（这里用电荷和自旋）
            f.write(f"charge={log_data['charge']} spin={log_data['spin_multiplicity']}\n")
            # 坐标
            for coord in log_data['coordinates']:
                f.write(f"{coord}\n")
                
        return xyz_file, log_data['charge'], log_data['spin_multiplicity']
    
    def generate_input(self, task_info: Dict, task_dir: str, output_dir: str) -> None:
        """
        生成 ORCA 输入文件
        """
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 解析 ORCA 块内容
            orca_lines = task_info['orca_block'].split('\n')
            source_task = None
            control_params = {}
            
            for line in orca_lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('%'):
                    # 提取源任务名
                    source_task = line.lstrip('%').strip()
                elif line.startswith('#'):
                    # 解析控制行
                    control_params = self._parse_control_line(line)
            
            if not source_task:
                raise ValueError("Source task not specified in ORCA block")
            if 'job' not in control_params:
                raise ValueError("Job type not specified in control line")
                
            # 加载模板
            template_name = control_params['job']
            if template_name not in self.templates_cache:
                self.templates_cache[template_name] = self._load_template(template_name)
            template = self.templates_cache[template_name]
            
            # 获取原始文件名（不包含路径和扩展名）
            task_files = [f for f in os.listdir(task_dir) if f.endswith('.task')]
            if not task_files:
                raise ValueError(f"No task file found in {task_dir}")
            original_file_name = os.path.splitext(task_files[0])[0]
            
            # 获取源任务的 log 文件，使用正确的命名格式
            source_log = os.path.join(
                task_dir, 
                source_task, 
                f"{source_task}_{original_file_name}.log"
            )
            
            if not os.path.exists(source_log):
                raise FileNotFoundError(f"Source log file not found: {source_log}")
                
            # 转换为 xyz 格式
            xyz_file, charge, spin = self._convert_log_to_xyz(source_log, output_dir)
            
            # 准备参数替换
            params = template['defaults'].copy()
            params.update(control_params)
            params['xyz_file'] = os.path.basename(xyz_file)
            
            # 生成输入文件
            output_inp = os.path.join(output_dir, f"{task_info['job_title']}.inp")
            with open(output_inp, 'w') as f:
                for line in template['content']:
                    # 替换所有占位符
                    for key, value in params.items():
                        line = line.replace(f"[{key}]", value)
                    # 替换电荷和自旋
                    line = line.replace("[charge]", str(charge))
                    line = line.replace("[spin]", str(spin))
                    f.write(f"{line}\n")
            
            logger.info(f"Generated ORCA input file: {output_inp}")
            
        except Exception as e:
            logger.error(f"Error generating ORCA input: {str(e)}")
            raise 