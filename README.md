# task自动计算程序使用说明

## 1. 内容
- task_module.py
- geom_extract.py
- smiles_parser.py
### 1.1 task_module.py
该脚本存放在*script_path2*，为driver脚本，负责解析任务块、调度其他脚本完成任务。
```python
# 定义脚本目录
script_path1 = os.path.expanduser('~/apprepo/gaussian/16-hy/scripts/python')
script_path2 = os.path.expanduser('~/apprepo/gaussian/16-hy/scripts/tasks')
# 定义日志目录
~/AutoCalc/tasks/task_processing.log
# 任务文件夹
TASKS_DIR = os.path.expanduser("~/AutoCalc/tasks")
```
task_module.py运行后，会对TASKS_DIR下的每个子文件夹的内容进行检查，若匹配到文件名相同的两个后缀名分别为.com与.task的文件，则按照task文件中的内容进行处理，生成Gaussian输入文件。该脚本运行时无需交互输入，适合放在*crontab*中定时运行
### 1.2 geom_extract.py
该脚本存放在*script_path1*目录，可以解析几何信息。支持提取Gaussian 16的输入与输出文件中的几何信息，但只会保留坐标信息，冻结信息等会丢失。

对于gjf文件，支持Chem3D导出的格式或GView导出的标准格式。

对于log文件，支持Standard orientation下的标准朝向坐标。对于使用了nosymm的情况，也支持Input orientation。
### 1.3 smiles_parser.py
该脚本存放在*script_path2*，依赖*rdkit*库和*requests*库。只有在几何信息以smiles字符串或CAS号的形式提供时才会启用，将其转换为3D结构，并使用MMFF94力场进行预优化，上限1000步。若MMFF94对当前体系不可用，则改用UFF力场。

若以CAS提供，则需连接外部网络，从pubChem提供的API接口转换为smiles结构
### (1.4 slurms.sh)
该脚本运行后会自定义文件夹下的尚未提交的gjf文件，可以作为task_module.py的上级脚本使用。

## 2. task文件语法
该文件可以定义多个以$开头的任务块，程序会依次进行处理:

    $task_name
    %opt
    # opt freq
### $
"$"作为一个任务块的开始，定义了该任务的名称。脚本处理该任务块时，会为其创建名为*task_name*的文件夹，对应输入文件均创建在该文件夹下。
### %
"%"指示了当前任务块几何信息的来源。脚本会寻找"%"指示的任务块文件夹，从该任务块的log文件中读取最后一帧的几何信息。暂不支持{}。预留关键词如下：
- %origin 表示从原始.com文件中读取几何信息
- %smiles=CCO 表示从smiles字符串(当前示例为乙醇)转换为3D结构。也支持在此处输入CAS号，嗯，我知道这很蠢。
### \#
"#"后的内容为你想要当前任务块使用的Gaussian任务关键词。特殊语法{}表示为{}内的每一个元素创建一个将{}整体替换为该元素的输入文件。
## 3. 待开发功能
- %支持指定目录文件
- 支持xyz格式文件
- 支持在当前任务结束后自动执行某些脚本，如fchk
- 支持判断震荡情况
- 与mail模块结合实时监控任务状况
