import os
from config import AUTOTASKER_WFN_PATH, AUTOTASKER_SCRIPTS_PATH

def parse_scripts(content):
    """处理 scripts=(a,b,c,...) 格式的命令。"""
    script_items = content.split(',')
    commands = []
    for item in script_items:
        item = item.strip()
        if item:
            commands.append(f"bash $tasker_scripts/{item}.sh")
    return commands

def parse_multiwfn(content):
    """处理 multiwfn=(input>template,...) 格式的命令。
    例如：multiwfn=(output.wfn>ESP,output.fchk>BOND)
    会生成命令：multiwfn ./output.wfn < $wfn_examples/ESP.txt
    """
    items = content.split(',')
    commands = []
    for item in items:
        item = item.strip()
        if '>' in item:
            template, input_file = item.split('>')
            input_file = input_file.strip()
            template = template.strip()
            # 生成 multiwfn 的命令
            commands.append(f"Multiwfn ./{input_file} < $wfn_examples/{template}.txt > mw_{template}_out.txt")
    return commands

def parse_copy(content):
    """
    处理 copy=(source>target,...) 格式的命令。
    source 可以是文件或目录，target 是目标路径。
    支持通配符 * 匹配。
    
    示例：
    copy=(output.log>../logs/,*.wfn>../wfn_files/)
    """
    items = content.split(',')
    commands = []
    for item in items:
        item = item.strip()
        if '>' in item:
            source, target = item.split('>')
            source = source.strip()
            target = target.strip()
            
            # 处理目标路径：如果目标路径是目录，确保它存在
            commands.append(f"mkdir -p {target}")
            
            # 根据源路径是否包含通配符选择不同的复制命令
            if '*' in source:
                # 使用 cp -r 来复制匹配的所有文件/目录
                commands.append(f"cp -r {source} {target}/")
            else:
                # 普通文件或目录的复制
                commands.append(f"cp -r {source} {target}/")
    return commands

def default_handler(command):
    """默认处理器，直接返回原始命令。"""
    return [command]

# 创建一个关键词到处理函数的映射表
COMMAND_DISPATCH = {
    "scripts": parse_scripts,
    "multiwfn": parse_multiwfn,
    "copy": parse_copy,
}

def handle_command(command):
    """根据命令的类型选择合适的处理函数。"""
    if '=' in command:
        key, content = command.split('=', 1)
        key = key.strip()
        content = content.strip("()")  # 去除括号
        if key in COMMAND_DISPATCH:
            return COMMAND_DISPATCH[key](content)  # 调用对应的处理函数
    return default_handler(command)  # 默认处理器

def parse_and_write_commands(commands, output_dir):
    """
    解析命令并将处理后的结果写入 comd 文件。
    """
    try:
        output_file = os.path.join(output_dir, 'comd')
        with open(output_file, 'w') as f:
            # 在文件开头写入 $tasker_scripts 和 $wfn_examples 变量定义
            f.write("# Command file generated by task processor\n")
            f.write(f"export tasker_scripts={AUTOTASKER_SCRIPTS_PATH}\n")
            f.write(f"export wfn_examples={AUTOTASKER_WFN_PATH}\n")
            f.write(f"# Multiwfn env\n")
            f.write(f"source $wfn_examples/env.sh\n\n")

            # 逐个解析并写入命令
            for command in commands:
                processed_commands = handle_command(command)
                for line in processed_commands:
                    f.write(line + "\n")

        print(f"Commands written to: {output_file}")

    except Exception as e:
        print(f"Failed to write commands: {e}")