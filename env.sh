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

# 定义tast命令函数
tast() {
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
        *)
            echo "Usage: tast [OPTION]"
            echo "Options:"
            echo "  --run, -r     Run test calculation"
            echo "  --build, -b   Run smiles build test"
            echo "  --comd, -c    Run command test"
            ;;
    esac
}

# 将tast函数导出为命令
export -f tast