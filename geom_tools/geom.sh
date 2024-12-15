#!/bin/bash

awk '
/Standard orientation:/ {
    delete coords  # 清空之前存储的坐标
    count = 0
    for(i=1; i<=4; i++) getline  # 跳过5行
    while(getline && !/-{10,}/) {  # 读到分隔线为止
        count++
        coords[count] = $2 " " $4 " " $5 " " $6
    }
}
END {  # 在文件结束时打印最后一组坐标
    for(i=1; i<=count; i++) print coords[i]
}' name.log