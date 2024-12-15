#!/bin/bash

# 获取脚本所在目录的完整路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 定义元素周期表映射数组
declare -A elements
elements=(
    [1]="H"   [2]="He"  [3]="Li"  [4]="Be"  [5]="B"   [6]="C"   [7]="N"   [8]="O"   [9]="F"   [10]="Ne"
    [11]="Na" [12]="Mg" [13]="Al" [14]="Si" [15]="P"  [16]="S"  [17]="Cl" [18]="Ar" [19]="K"  [20]="Ca"
    [21]="Sc" [22]="Ti" [23]="V"  [24]="Cr" [25]="Mn" [26]="Fe" [27]="Co" [28]="Ni" [29]="Cu" [30]="Zn"
    [31]="Ga" [32]="Ge" [33]="As" [34]="Se" [35]="Br" [36]="Kr" [37]="Rb" [38]="Sr" [39]="Y"  [40]="Zr"
    [41]="Nb" [42]="Mo" [43]="Tc" [44]="Ru" [45]="Rh" [46]="Pd" [47]="Ag" [48]="Cd" [49]="In" [50]="Sn"
    [51]="Sb" [52]="Te" [53]="I"  [54]="Xe" 
    # 可以根据需要添加更多元素
)

# 获取当前目录中的log文件
log_file=$(ls *.log 2>/dev/null | head -n 1)
if [ -z "$log_file" ]; then
    echo "Error: No .log file found in current directory"
    exit 1
fi

# 创建optDFTw目录
optdftw_dir="../optDFTw"
mkdir -p "$optdftw_dir"

# 创建临时文件
temp_file=$(mktemp)
temp_coord_file=$(mktemp)

# 提取电荷和自旋多重度
charge_multi=$(grep "Charge =" "$log_file" | tail -n 1)
charge=$(echo "$charge_multi" | awk '{print $3}')
multiplicity=$(echo "$charge_multi" | awk '{print $6}')

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

# 创建template.gjf文件
{
    echo "#p LC-wPBE/TZVP"
    echo ""
    echo "Template for optDFTw"
    echo ""
    echo "$charge $multiplicity"
    
    # 处理坐标，将原子序数转换为元素符号
    while read -r line; do
        atomic_num=$(echo "$line" | awk '{print $1}')
        x=$(echo "$line" | awk '{print $2}')
        y=$(echo "$line" | awk '{print $3}')
        z=$(echo "$line" | awk '{print $4}')
        element="${elements[$atomic_num]:-$atomic_num}"
        echo "$element $x $y $z"
    done < "$temp_coord_file"
    
    echo ""
    echo ""
} > "$optdftw_dir/template.gjf"

# 创建comd文件
cat > "$optdftw_dir/comd" << 'EOF'
./optDFTw 0.01 0.1 0.05 0.0001 > optDFTw.out
EOF

# 复制所需文件
if [ -d "$(dirname $SCRIPT_DIR)/External_Programs/optDFTw" ]; then
    cp -r "$(dirname $SCRIPT_DIR)/External_Programs/optDFTw"/* "$optdftw_dir/"
    echo "Successfully copied optDFTw files"
else
    echo "Error: optDFTw source directory not found"
    exit 1
fi

# 清理临时文件
rm -f "$temp_file" "$temp_coord_file"

echo "optDFTw setup completed successfully"