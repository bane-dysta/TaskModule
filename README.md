# task自动计算程序使用说明

## 1. 内容
- task_module.py
- geom_extract.py
- smiles_parser.py
### 1.1 task_module.py
该脚本存放在*script_path2*，为main脚本，负责解析任务块、调度其他脚本完成任务。
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
因历史原因，该脚本存放在*script_path1*目录，可以解析几何信息。支持提取Gaussian 16的输入与输出文件中的几何信息，但只会保留坐标信息，冻结信息等会丢失。

对于gjf文件，支持Chem3D导出的格式或GView导出的标准格式。

对于log文件，支持Standard orientation下的标准朝向坐标。对于使用了nosymm的情况，也支持Input orientation。
### 1.3 smiles_parser.py
该脚本存放在*script_path2*，依赖*rdkit*库和*requests*库。只有在几何信息以smiles字符串或CAS号的形式提供时才会启用，将其转换为3D结构，并使用MMFF94力场进行预优化，上限1000步。若MMFF94对当前体系不可用，则改用UFF力场。

若以CAS提供，则需连接外部网络，从pubChem提供的API接口转换为smiles结构。

### 1.4 commands_words.py
该脚本存放在*script_path2*，控制命令词模块的输出。有关命令词模块，参见第二节"!"部分。

### 1.5 task_generator.py
该脚本存放在*script_path2*，在task_module.py匹配到task对后，检查task文件内容，如文件内容为
~~~
@txt=example
~~~
则前往环境变量GAUSSIAN_TEMPLATE_DIR目录下寻找example.txt，把对应内容复制到当前task文件中并替换原内容。

### (1.6 slurms.sh)
该脚本运行后会自定义文件夹下的尚未提交的gjf文件，可以作为task_module.py的上级脚本使用。

## 2. task文件语法
该文件可以定义多个以$开头的任务块，程序会依次进行处理:

    $task_name
    %opt
    ! scripts=(fchk) multiwfn=(hole=*.fchk,uvvis=*.log)
    # opt freq
### $
"$"作为一个任务块的开始，定义了该任务的名称。脚本处理该任务块时，会为其创建名为*task_name*的文件夹，对应输入文件均创建在该文件夹下。
### %
"%"指示了当前任务块几何信息的来源。脚本会寻找"%"指示的任务块文件夹，从该任务块的log文件中读取最后一帧的几何信息。暂不支持{}。预留关键词如下：
- %origin 表示从原始.com文件中读取几何信息
- %smiles=CCO 表示从smiles字符串(当前示例为乙醇)转换为3D结构。也支持在此处输入CAS号，嗯，我知道这很蠢。
### \#
"#"后的内容为你想要当前任务块使用的Gaussian任务关键词。特殊语法{}表示为{}内的每一个元素创建一个将{}整体替换为该元素的输入文件。
### !
"!"是特殊语法，目前需要与slurms脚本结合才能发挥作用。作用是将命令词解析为bash命令，输出到任务目录下的comd文件中。slurms脚本运行时会尝试读取comd文件，将其中内容复制到slurm脚本末尾，如此即可实现任务结束后自动调用multiwfn分析或是自定义命令。目前仅支持四种命令词：
- scripts：语法为scripts=(a,b,c,d,...)，脚本解析后会转换为运行指定环境变量TASKSCRIPTS_PATH目录下的脚本：
  ~~~
  bash $Taskscripts/a.sh
  bash $Taskscripts/b.sh
  ...
  ~~~
  推荐写个formchk *.chk，可以配合multiwfn使用
- multiwfn：语法为multiwfn=(a>b,c>d,...)，脚本解析后会生成multiwfn命令
  ~~~
  Multiwfn b < $wfn_examples/a.txt > mw_a_out.txt
  Multiwfn d < $wfn_examples/c.txt > mw_c_out.txt
  ~~~
  其中，$wfn_examples变量可以通过export环境变量WFN_EXAMPLES_PATH来设置。
- copy：语法为copy=(source1>target1,source2>target2,...)，支持*通配符。
- 其他：原封不动复制到comd文件内。

## 3. 待开发功能
- %source可支持以指定目录文件为source
- 支持xyz格式文件
- ~~支持在当前任务结束后自动执行某些脚本，如fchk~~ 已完成
- 支持判断震荡情况
- 与mail模块结合实时监控任务状况
- ~~支持自动用multiwfn分析~~ 已完成