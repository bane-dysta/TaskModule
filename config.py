import os

# 全局路径
AUTOTASKER_BASE_PATH = os.path.abspath(os.path.dirname(__file__))
AUTOTASKER_CALC_PATH = os.path.expanduser("~/AutoCalc/tasks")

# 其他可用路径变量或参数可在这里定义
AUTOTASKER_LOG_PATH = os.path.join(AUTOTASKER_CALC_PATH, "task_processing.log")

AUTOTASKER_WFN_PATH = os.path.join(AUTOTASKER_BASE_PATH, "wfntxts")
AUTOTASKER_TEMPLATES_PATH = os.getenv('GAUSSIAN_TEMPLATE_DIR', os.path.join(AUTOTASKER_BASE_PATH, "templates"))
AUTOTASKER_GEOMTOOLS_PATH = os.path.join(AUTOTASKER_BASE_PATH, "geom_tools")
AUTOTASKER_SCRIPTS_PATH = os.path.join(AUTOTASKER_BASE_PATH, "scripts")