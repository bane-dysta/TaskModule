#!/bin/bash

echo "Current time: $(date)"
# 输入文件夹的路径
input_folder="$HOME/AutoCalc"  # 根据需要修改此路径

# 加载必要的环境变量和模块
source /etc/profile
source $HOME/miniconda/etc/profile.d/conda.sh
conda activate rdkitenv

# 检查 Python 脚本是否存在
if [ -f "$HOME/scripts/tasks/task_module.py" ]; then
    python3 $HOME/scripts/tasks/task_module.py  # 调用Python脚本
else
    echo "Error: Python script $HOME/scripts/tasks/task_module.py not found."
fi

# 初始化一个空的数组来存储未处理的文件
input_files=()

# 递归搜索所有.gjf文件
while IFS= read -r file; do
    log_file="${file%.gjf}.log"  # 构建对应的.log文件名
    base_name=$(basename "$file")  # 获取文件的基本名（不含路径）
    
    if [ ! -f "$log_file" ] && [ "$base_name" != "template.gjf" ]; then  # 检查.log文件是否存在且文件名不是template.gjf
        input_files+=("$file")  # 如果条件满足，添加到数组
    fi
done < <(find "$input_folder" -type f -name "*.gjf")

# 获取当前用户的所有作业
current_jobs=$(squeue -u $USER -o "%.18i %.100j" | awk '{print $2}' | grep -o '^[^[:space:]]*')

# 过滤出那些还没有提交到 SLURM 队列中的文件
queue_filtered_files=()
for file in "${input_files[@]}"; do
    base_name=$(basename "$file" .gjf)
    if ! grep -q "$base_name" <<< "$current_jobs"; then
        queue_filtered_files+=("$file")
    fi
done

# 打印最终将提交的文件列表
echo "Files to be submitted:"
printf "%s\n" "${queue_filtered_files[@]}"

# 获取可用的第一个分区
partition_name=$(sinfo -h -o %P | head -n 1)

if [ -z "$partition_name" ]; then
    echo "Error: No partitions available."
    exit 1
fi

echo "Using partition: $partition_name"

# 确保日志文件夹存在
mkdir -p "$HOME/.sub"

# 提交作业的函数
submit_job() {
    local input_file="$1"
    local input_dir=$(dirname "$input_file")  # 提取文件所在的目录
    local log_file="${input_file%.gjf}.log"
    local file_name=$(basename "$input_file" .gjf)
    local chk_file="${input_file%.gjf}.chk"  # 与输入文件和log文件相同的目录
    local comd_file="$input_dir/comd"  # comd文件路径

    # 切换到文件所在的目录
    if cd "$input_dir"; then
        echo "Switched to directory $input_dir"
    else
        echo "Error: Failed to switch to directory $input_dir"
        return 1
    fi

    # 修改chk路径
    if grep -q "%chk" "$input_file"; then
        sed -i "s|%chk=.*|%chk=${chk_file}|" "$input_file"
    fi

    local job_script="${input_file%.gjf}.sh"
    
    # 创建基本的作业脚本
    cat > "$job_script" <<EOF
#!/bin/bash
#SBATCH -J ${file_name}
#SBATCH --ntasks=32
#SBATCH -N 1
#SBATCH --mem=100000M  
#SBATCH -p $partition_name
source $HOME/apprepo/gaussian/16-hy/scripts/env.sh  # 确保这条路径是正确的
export PGI_FASTMATH_CPU=sandybridge
g16 "$input_file" > "$log_file"
EOF

    # 检查是否存在comd文件，如果存在则添加到作业脚本末尾
    if [ -f "$comd_file" ]; then
        echo "Found comd file, appending its contents to job script..."
        echo -e "\n# Commands from comd file" >> "$job_script"
        cat "$comd_file" >> "$job_script"
    fi

    local job_output=$(sbatch "$job_script")
    local job_id=$(echo "$job_output" | awk '{print $4}')
    echo "Submitted batch job $job_id for $input_file"
    rm "$job_script"  # 删除作业脚本以清理

    # 记录到日志文件
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Job $job_id: $input_file" >> "$HOME/.sub/submit.log"
    
    # 切换回到原来的路径
    cd - >/dev/null  # 切换回之前的目录，隐藏cd的输出
}

# 主逻辑，维持至少10个作业
current_jobs=$(squeue -u $USER | wc -l)
jobs_needed=20
jobs_to_submit=$((jobs_needed - current_jobs + 1)) # 加1是因为squeue输出包含了标题行

echo "Current jobs in queue: $current_jobs. Need to submit $jobs_to_submit additional jobs."

for i in $(seq 0 $((jobs_to_submit - 1))); do
    sleep 2
    if [ ${#queue_filtered_files[@]} -eq 0 ]; then
        echo "No more input files to submit."
        break
    fi
    submit_job "${queue_filtered_files[$i]}"
    queue_filtered_files=("${queue_filtered_files[@]:1}") # 移除已提交的文件
done

echo "Submission process completed."