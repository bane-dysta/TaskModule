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
            python "$AUTOTASKER_BASE_PATH/task_module.py"
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
            echo "  --run, -r                Process tasks in specified directory"
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
