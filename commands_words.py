import os

# 配置：定义路径变量（修改路径时只需修改这里）
TASKSCRIPTS_PATH = "/work/home/gaus7/Taskscripts"
WFN_EXAMPLES_PATH = "/work/home/gaus7/wfn_examples"  # 定义 wfn_examples 的路径

def parse_scripts(content):
    """处理 scripts=(a,b,c,...) 格式的命令。"""
    script_items = content.split(',')
    commands = []
    for item in script_items:
        item = item.strip()
        if item:
            commands.append(f"bash $Taskscripts/{item}.sh")
    return commands

def parse_multiwfn(content):
    """处理 multiwfn=(a=b,c=d,...) 格式的命令。"""
    items = content.split(',')
    commands = []
    for item in items:
        key_value = item.split('=')
        if len(key_value) == 2:  # 检查是否为 a=b 格式
            a, b = key_value[0].strip(), key_value[1].strip()
            # 生成 multiwfn 的命令
            commands.append(f"multiwfn ./{b} < $wfn_examples/{a}.txt")
    return commands

def parse_copy(content):
    """处理 copy=(...) 格式的命令。"""
    items = content.split(',')
    return [f"Copying data: {item.strip()}" for item in items if item.strip()]

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
            # 在文件开头写入 $Taskscripts 和 $wfn_examples 变量定义
            f.write("Parsed Commands:\n")
            f.write(f"export Taskscripts={TASKSCRIPTS_PATH}\n")
            f.write(f"export wfn_examples={WFN_EXAMPLES_PATH}\n\n")

            # 逐个解析并写入命令
            for command in commands:
                processed_commands = handle_command(command)
                for line in processed_commands:
                    f.write(line + "\n")

        print(f"Commands written to: {output_file}")

    except Exception as e:
        print(f"Failed to write commands: {e}")
