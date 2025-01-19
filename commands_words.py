import os

# 从环境变量获取路径
AUTOTASKER_WFN_PATH = os.getenv('AUTOTASKER_WFN_PATH')
AUTOTASKER_SCRIPTS_PATH = os.getenv('AUTOTASKER_SCRIPTS_PATH')

def parse_scripts(content):
    """处理 scripts=(script[,args]|script[,args]|...) 格式的命令。
    
    例如：
    scripts=(fchk|VIBRONIC,1,2|ESP,arg1)
    会生成命令：
    bash $tasker_scripts/fchk.sh
    bash $tasker_scripts/VIBRONIC.sh 1 2
    bash $tasker_scripts/ESP.sh arg1
    """
    script_items = content.split('|')
    commands = []
    for item in script_items:
        item = item.strip()
        if not item:
            continue
            
        # 分割脚本名和参数
        parts = item.split(',')
        script_name = parts[0].strip()
        args = [arg.strip() for arg in parts[1:]]  # 获取额外参数
        
        # 构建基本命令
        base_cmd = f"bash $tasker_scripts/{script_name}.sh"
        
        # 如果有参数，添加到命令中
        if args:
            args_str = ' '.join(args)
            base_cmd = f"{base_cmd} {args_str}"
            
        commands.append(base_cmd)
    return commands

def parse_multiwfn(content):
    """处理 multiwfn=(template>input[,args]|template>input[,args],...) 格式的命令。
    
    注意：> 号前后的含义：
    - > 号前面是模板文件名（不带.txt后缀）
    - > 号后面是要分析的波函数文件（可以用通配符 *）
    
    例如：
    multiwfn=(hole123>*.fchk|fmo>*.fchk|Eorb>*.fchk)
    会生成命令：
    multiwfn ./*.fchk < $wfn_examples/hole123.txt > mw_hole123_out.txt
    multiwfn ./*.fchk < $wfn_examples/fmo.txt > mw_fmo_out.txt
    multiwfn ./*.fchk < $wfn_examples/Eorb.txt > mw_Eorb_out.txt
    """
    items = content.split('|')
    commands = []
    for item in items:
        item = item.strip()
        if not item:
            continue
            
        # 分割命令和参数
        parts = item.split(',')
        main_command = parts[0].strip()
        args = [arg.strip() for arg in parts[1:]]  # 获取额外参数
        
        if '>' in main_command:
            template, input_file = main_command.split('>')  # 注意：template在前，input_file在后
            template = template.strip()
            input_file = input_file.strip()
            
            # 构建基本命令
            base_cmd = f"Multiwfn ./{input_file} < $wfn_examples/{template}.txt"
            
            # 如果有额外参数，添加到命令中
            if args:
                args_str = ' '.join(args)
                base_cmd = f"{base_cmd} {args_str}"
            
            # 添加输出重定向
            base_cmd = f"{base_cmd} > mw_{template}_out.txt"
            commands.append(base_cmd)
            
    return commands

def parse_copy(content):
    """
    处理 copy=(source>target|source>target,...) 格式的命令。
    source 可以是文件或目录，target 是目标路径。
    支持通配符 * 匹配。
    
    示例：
    copy=(output.log>../logs|*.wfn>../wfn_files)
    """
    items = content.split('|')
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

def parse_move(content):
    """
    处理 move=(source>target|source>target,...) 格式的命令。
    source 可以是文件或目录，target 是目标路径。
    支持通配符 * 匹配。
    """
    items = content.split('|')
    commands = []
    for item in items:
        item = item.strip()
        if '>' in item:
            source, target = item.split('>')
            source = source.strip()
            target = target.strip()
            
            # 首先创建目标目录
            commands.append(f"mkdir -p {target}")
            
            # 移动文件，确保目标路径以 / 结尾
            target = target if target.endswith('/') else target + '/'
            commands.append(f"mv {source} {target}")
    return commands

def parse_convtest(content, task_name=None):
    """处理 convtest 命令。
    将任务路径写入 ~/.sub/conv_test_list.txt 文件，并生成检查和移除的命令。
    
    Args:
        content: 命令内容
        task_name: 当前任务名称
        
    Returns:
        list: 包含检查和移除命令的列表
    """
    # 确保 ~/.sub 目录存在
    sub_dir = os.path.expanduser("~/.sub")
    os.makedirs(sub_dir, exist_ok=True)
    
    # 获取当前工作目录的绝对路径
    base_path = os.path.abspath(os.getcwd())
    
    # 如果有任务名，添加到路径中
    if task_name:
        abs_path = os.path.join(base_path, task_name)
    else:
        abs_path = base_path
        
    # 写入路径到文件
    conv_test_file = os.path.join(sub_dir, "conv_test_list.txt")
    with open(conv_test_file, "a") as f:
        f.write(f"{abs_path}\n")
    
    # 生成检查和移除的命令
    escaped_path = abs_path.replace('"', '\\"')  # 转义双引号
    commands = [
        f'if grep -q "^{escaped_path}$" ~/.sub/conv_test_list.txt; then',
        '    grep -v "^' + escaped_path + '$" ~/.sub/conv_test_list.txt > ~/.sub/conv_test_list.txt.tmp',
        '    mv ~/.sub/conv_test_list.txt.tmp ~/.sub/conv_test_list.txt',
        'fi'
    ]
    
    return commands

def default_handler(command):
    """默认处理器，直接返回原始命令。"""
    return [command]

# 创建一个关键词到处理函数的映射表
COMMAND_DISPATCH = {
    "scripts": parse_scripts,
    "multiwfn": parse_multiwfn,
    "copy": parse_copy,
    "move": parse_move,  # 添加新的 move 命令处理器
    "convtest": parse_convtest,  # 添加新的 convtest 命令处理器
}

def handle_command(command, task_name=None):
    """根据命令的类型选择合适的处理函数。"""
    if '=' in command:
        key, content = command.split('=', 1)
        key = key.strip()
        content = content.strip("()")  # 去除括号
        if key in COMMAND_DISPATCH:
            if key == "convtest":
                return COMMAND_DISPATCH[key](content, task_name)  # 对于 convtest 命令传递任务名
            return COMMAND_DISPATCH[key](content)  # 调用对应的处理函数
    return default_handler(command)  # 默认处理器

def parse_and_write_commands(commands, output_dir, task_name=None):
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
                processed_commands = handle_command(command, task_name)
                if processed_commands is not None:  # 只有当返回值不是 None 时才写入
                    for line in processed_commands:
                        f.write(line + "\n")

        print(f"Commands written to: {output_file}")

    except Exception as e:
        print(f"Failed to write commands: {e}")
        