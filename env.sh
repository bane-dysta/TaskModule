#!/bin/bash

# 设置基础路径
export AUTOTASKER_BASE_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export AUTOTASKER_CALC_PATH="$HOME/AutoCalc/tasks"

# 设置日志路径
export AUTOTASKER_LOG_PATH="$AUTOTASKER_CALC_PATH/task_processing.log"

# 设置其他相关路径
export AUTOTASKER_WFN_PATH="$AUTOTASKER_BASE_PATH/wfntxts"
export AUTOTASKER_TEMPLATES_PATH="${GAUSSIAN_TEMPLATE_DIR:-$AUTOTASKER_BASE_PATH/templates}"
export AUTOTASKER_GEOMTOOLS_PATH="$AUTOTASKER_BASE_PATH/geom_tools"
export AUTOTASKER_SCRIPTS_PATH="$AUTOTASKER_BASE_PATH/scripts"

export tasker="$AUTOTASKER_BASE_PATH"

# 定义tasker命令函数
tasker() {
    case "$1" in
        --run|-r)
            if [ -n "$2" ]; then
                # 获取输入路径的父目录
                parent_dir=$(dirname "$2")
                python "$AUTOTASKER_BASE_PATH/task_module.py" "$parent_dir"
            else
                python "$AUTOTASKER_BASE_PATH/task_module.py"
            fi
            ;;
        --gen|-g)
            if [ -n "$3" ]; then
                # 有输入文件和模板名
                python "$AUTOTASKER_BASE_PATH/case/tasker_gen_fromtxt.py" "$2" "$3"
            elif [ -n "$2" ]; then
                # 只有输入文件
                python "$AUTOTASKER_BASE_PATH/case/tasker_gen_fromtxt.py" "$2"
            else
                # 无参数
                python "$AUTOTASKER_BASE_PATH/case/tasker_gen_fromtxt.py"
            fi
            ;;
        --redo|-re)
            # 在当前目录搜索 .task 文件
            task_files=$(find . -maxdepth 1 -name "*.task")
            if [ -z "$task_files" ]; then
                echo "No .task files found in current directory"
                return 1
            fi
            
            for task_file in $task_files; do
                if [ -n "$2" ]; then
                    # 如果提供了参数，只移除匹配的任务名的双引号
                    sed -i "s/\$\"$2\"/\$$2/" "$task_file"
                else
                    # 移除所有任务名的双引号
                    sed -i 's/\$"\([^"]*\)"/\$\1/' "$task_file"
                fi
                echo "Processed $task_file"
            done
            ;;
        --smiles|-s)
            python "$AUTOTASKER_BASE_PATH/case/test_SmilesBuild.py"
            ;;
        --comd|-c)
            python "$AUTOTASKER_BASE_PATH/case/test_comd.py" "$2"
            ;;
        --test|-t)
            python "$AUTOTASKER_BASE_PATH/case/test_calc.py"
            ;;
        --all-comd|-ac)
            python "$AUTOTASKER_BASE_PATH/case/all_comd.py"
            ;;
        --help|-h)
            echo "Usage: tasker [OPTION] [ARGS]"
            echo "Options:"
            echo "  --run, -r [task_dir]     Process tasks in task_dir's parent directory"
            echo "                           If task_dir is not provided, use default path"
            echo "  --gen, -g [input_file] [template]  Generate task from template in current directory"
            echo "                           input_file: Optional, use first log file if not provided"
            echo "                           template: Optional, template name in templates directory"
            echo "  --redo, -re [task_name]  Remove quotes from task names in current directory"
            echo "                           If task_name is provided, only remove quotes from matching tasks"
            echo "  --smiles, -s             Build smiles"
            echo "  --comd, -c [commands]    Run command test or process command string"
            echo "                           Example: tasker -c \"scripts=(fchk) copy=(*.fchk>../FCclasses)\""
            echo "  --all-comd, -ac          Run all commands"
            echo "  --test, -t               Build test calculation"
            echo "  --help, -h               Show this help message"
            echo "Info:"
            echo "Environment variable 'tasker' has been set."
            ;;
        *)
            tasker --help
            ;;
    esac
}

# 将tasker函数导出为命令
export -f tasker
