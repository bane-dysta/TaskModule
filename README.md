# Tasker: Gaussian计算任务自动化工具集

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/yourusername/gaussian-automation)
[![Python](https://img.shields.io/badge/python-3.6+-yellow.svg)](https://www.python.org/)

## 💡简介

Tasker是一套Python脚本工具集，用于自动化生成Gaussian计算任务。特性：
- 处理复杂的任务依赖，按照要求生成输入文件
- 任务模块化，通过建立模板库轻松设置复杂的计算任务
- 结合crontab，按照task文件自动进行计算
- 结合作业调度系统，实现通过调用Multiwfn或运行自定义脚本等方式进行自动后处理

Tasker套件有配套可视化工具Orbital viewer，支持在Windows平台下对轨道进行一键可视化。
## 🔧运行环境
- 系统：Linux(谁家量化计算在Windows上做啊)
- 网络需求：在以CAS号形式输入结构时，需要连接网络调用PubChem的API接口
- 环境依赖：
  - 开发环境python 3.8，理论上兼容python3
  - 若以smiles字符串形式输入结构，需要rdkit库
  - 若以CAS号形式输入结构，需要rdkit和requests库
- 环境变量：
  ```bash
  export AUTOTASKER_CALC_PATH="/path/to/calc_folder"
  ```

## 🚀快速开始

要设置一项计算，您可以在``AUTOTASKER_CALC_PATH``建立一个文件夹，该文件夹就是存放您计算任务相关所有文件的路径。您需要选择一种方式给出分子结构，tasker目前支持：

 - com/gjf文件：Gaussian标准输入格式，可以没有关键词等信息，但要有正确的几何坐标、电荷和自旋多重度。推荐使用com文件，因为gjf是配套``slurms.sh``脚本识别的后缀，会被自动提交。
 - smiles字符串/CAS号：在task文件中以"%smiles="的形式给出，此时com文件内可以不提供几何坐标。

``name.task``文件是管理计算任务的文件，文件名应与您的com文件相同。您可以参照下一节的说明手动设置该文件，也可以引用模板库中的文件。例如，在tasker目录下的templates文件夹中寻找fluor.txt，并使用该计算模板：
```
@txt=fluor
```

设置完毕后，运行task_module.py，程序会识别AUTOTASKER_CALC_PATH的子目录下文件名相同的一对(task,com/gjf)文件，按照task文件中的设定来生成gjf文件。推荐结合作业调度系统和crontab使用，以达到全自动生成、提交计算任务的目的。

## ⚙️任务文件语法

### 任务名(`$`)

任务文件由任务块许多任务块构成，每个任务块都由`$`起始，这也是脚本识别任务块的依据。脚本生成gjf文件时，会将任务名作为前缀附加到原始com/gjf文件名前作为新的gjf文件名。以下是任务块结构示例：
```
$task_name            # 任务名
%source               # 结构来源
! commands            # 命令指令
# gaussian_keywords   # 计算关键词
add = density.wfn     # 读取额外输入
```

### 结构来源 (`%`)
支持以下几种方式提供几何结构：
```
%origin             # 使用初始com/gjf中的结构
%smiles=CCO         # 使用SMILES生成
%smiles=50-00-0     # 使用CAS号生成
%task_name          # 使用其他任务的计算结果
%restart            # 重新提交该任务(注意！这会覆盖当前任务。)
```

%task_name是最频繁使用的结构来源，这会请求tasker从任务名为task_name的任务正常结束的输出文件中提取最后一帧的结构。例如：
```
$opt
%origin
# opt freq b3lyp/6-31g*

$td
%opt
# td(nstate=10) wb97xd/def2tzvp
```
在第二个任务块中，%opt请求从第一个任务正常结束的log文件中提取几何坐标，并作为该任务的起始坐标使用。

### 命令词 (`!`)
命令词由commands_words.py解析，并将bash命令写入名为comd的文件内。slurms.sh提交任务时会识别该comd文件，将其中内容复制到slurm脚本中，以实现自动化后处理。目前支持以下命令类型：

#### scripts命令
```
scripts=(fchk,esp)
```

该命令词会请求打印一条可以执行tasks/scripts目录下同名bash脚本的bash命令。支持多个脚本按顺序执行。

#### multiwfn命令

```bash
multiwfn=(output.fchk>hole,output.log>uvvis)
```

该命令词会请求一条以tasks/wfntxts下的txt模板运行multiwfn进行后处理的bash命令，该会同时source目录下multiwfn的环境变量文件env.sh。
- 支持通配符。
- multiwfn的输出将被重定向到`mw_{template}_out.txt`。

#### copy和move命令

```
copy=(*.log>../logs/,*.fchk>../analysis/)
move=(*.log>../logs/,*.fchk>../analysis/)
```
该命令词会请求一条将对应文件复制或移动到指定目录的bash命令，用来整理计算文件。
- 支持通配符
- 自动创建目标目录

## 外部程序
External_Programs目录下挂载了sobereva老师的[optDFTw](http://bbs.keinsci.com/forum.php?mod=viewthread&tid=4100&fromuid=63020)和[sobMECP](http://bbs.keinsci.com/forum.php?mod=viewthread&tid=865&fromuid=63020)(sobMECI是sobMECP的魔改版)，可以通过scripts命令进行调用。如果您使用这两个程序计算并用于发表，还需要按照sobereva老师的要求进行引用。

## 🔰开发计划

- [ ] 支持以指定目录文件为结构资源
- [ ] 支持xyz、log格式文件
- [ ] 支持判断震荡情况
- [ ] 与mail模块结合实时监控任务状况

## 🙏致谢

- [Multiwfn](http://sobereva.com/multiwfn) - 强大的波函数分析工具
- [RDKit](https://www.rdkit.org/) - 分子操作工具库
- [PubChem](https://pubchem.ncbi.nlm.nih.gov/) - 化学数据库

> Author: Bane Dysta  
> Email: banerxmd@gmail.com   
> Website: https://bane-dysta.github.io/
