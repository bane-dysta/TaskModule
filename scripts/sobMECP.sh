#!/bin/bash

# 获取脚本所在目录的完整路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 获取当前目录中的log文件
log_file=$(ls *.log 2>/dev/null | head -n 1)
if [ -z "$log_file" ]; then
    echo "Error: No .log file found in current directory"
    exit 1
fi

# 获取原始文件名（不含扩展名）
original_file_name=$(basename "$log_file" .log)

# 设置目标目录
target_dir="$HOME/work/sobMECP_${original_file_name}"

# 创建目标目录（如果不存在）
mkdir -p "$target_dir"

# 如果目录是新创建的或为空，则复制sobMECP文件
if [ -z "$(ls -A "$target_dir")" ]; then
    if [ -d "$(dirname $SCRIPT_DIR)/sobMECP" ]; then
        cp -r "$(dirname $SCRIPT_DIR)/sobMECP"/* "$target_dir/"
        echo "Copied sobMECP files to $target_dir"
    else
        echo "Error: sobMECP source directory not found"
        exit 1
    fi
else
    echo "Target directory already exists and is not empty, skipping file copy"
fi

# 创建临时文件
temp_coord_file=$(mktemp)

# 提取最后一个Standard orientation的坐标
awk '
/Standard orientation:/ {
    delete coords
    count = 0
    for(i=1; i<=4; i++) getline
    while(getline && !/-{10,}/) {
        count++
        coords[count] = $2 " " $4 " " $5 " " $6
    }
}
END {
    if (count > 0) {
        for(i=1; i<=count; i++) print coords[i]
    }
}' "$log_file" > "$temp_coord_file"

# 如果没有找到Standard orientation，尝试Input orientation
if [ ! -s "$temp_coord_file" ]; then
    awk '
    /Input orientation:/ {
        delete coords
        count = 0
        for(i=1; i<=4; i++) getline
        while(getline && !/-{10,}/) {
            count++
            coords[count] = $2 " " $4 " " $5 " " $6
        }
    }
    END {
        if (count > 0) {
            for(i=1; i<=count; i++) print coords[i]
        }
    }' "$log_file" > "$temp_coord_file"
fi

# 确定输出文件名
if [ -f "$target_dir/geom" ]; then
    output_file="$target_dir/geom_1"
else
    output_file="$target_dir/geom"
fi

# 将坐标写入输出文件
cat "$temp_coord_file" > "$output_file"

# 清理临时文件
rm -f "$temp_coord_file"

echo "Geometry information has been written to $output_file"