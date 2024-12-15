import os

def get_env_or_default(var_name, default_value):
    return os.getenv(var_name, default_value)

# 定义默认值
DEFAULT_BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CALC_PATH = os.path.expanduser("~/AutoCalc/tasks")

# 获取环境变量或使用默认值
AUTOTASKER_BASE_PATH = get_env_or_default('AUTOTASKER_BASE_PATH', DEFAULT_BASE_PATH)
AUTOTASKER_CALC_PATH = get_env_or_default('AUTOTASKER_CALC_PATH', DEFAULT_CALC_PATH)
AUTOTASKER_LOG_PATH = get_env_or_default('AUTOTASKER_LOG_PATH', 
                                        os.path.join(AUTOTASKER_CALC_PATH, 'task_processing.log'))
AUTOTASKER_WFN_PATH = get_env_or_default('AUTOTASKER_WFN_PATH', 
                                        os.path.join(AUTOTASKER_BASE_PATH, 'wfntxts'))
AUTOTASKER_TEMPLATES_PATH = get_env_or_default('AUTOTASKER_TEMPLATES_PATH', 
                                             os.path.join(AUTOTASKER_BASE_PATH, 'templates'))
AUTOTASKER_GEOMTOOLS_PATH = get_env_or_default('AUTOTASKER_GEOMTOOLS_PATH', 
                                              os.path.join(AUTOTASKER_BASE_PATH, 'geom_tools'))
AUTOTASKER_SCRIPTS_PATH = get_env_or_default('AUTOTASKER_SCRIPTS_PATH', 
                                            os.path.join(AUTOTASKER_BASE_PATH, 'scripts'))