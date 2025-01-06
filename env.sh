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
            python "$AUTOTASKER_BASE_PATH/case/test_calc.py"
            ;;
        --build|-b)
            python "$AUTOTASKER_BASE_PATH/case/test_SmilesBuild.py"
            ;;
        --comd|-c)
            python "$AUTOTASKER_BASE_PATH/case/test_comd.py"
            ;;
        --task|-t)
            python "$AUTOTASKER_BASE_PATH/task_module.py"
            ;;

        --help|-h)
            echo "Usage: tasker [OPTION]"
            echo "Options:"
            echo "  --run, -r              Run test calculation"
            echo "  --build, -b            Run smiles build test"
            echo "  --comd, -c             Run command test"
            echo "  --task, -t <task_dir>  Process tasks in specified directory"
            echo "  --help, -h             Show this help message"
            ;;
        *)
            tasker --help
            ;;
    esac
}

# 将tasker函数导出为命令
export -f tasker
