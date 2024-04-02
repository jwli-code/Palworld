import sys
import pandas as pd

def find_next_cluster(data, existing_clusters):
    # 初始化最大总和和对应的列名
    max_sum = 0
    max_sum_column = None

    # 计算所有现有cluster的总和
    cluster_sum = data[existing_clusters].sum(axis=1)

    # 对于每个样本（列），进行转换并计算总和
    for column in data.columns:
        if column not in existing_clusters:
            # 将样本列与所有现有cluster的总和相加
            temp = data[column] + cluster_sum
            # 转换值
            temp = temp.apply(lambda x: 1 if x >= 1 else 0)
            # 计算总和
            temp_sum = temp.sum()
            # 检查是否是最大总和
            if temp_sum > max_sum:
                max_sum = temp_sum
                max_sum_column = column

    return max_sum_column, max_sum

def process_data(input_file, output_file, num_clusters):
    # 读取数据
    data = pd.read_csv(input_file, index_col=0, sep='\t')

    # 初始化cluster列表
    clusters = []

    # 依次找出每个cluster
    for _ in range(num_clusters):
        next_cluster, cluster_sum = find_next_cluster(data, clusters)
        if next_cluster:
            clusters.append(next_cluster)
            with open(output_file, 'a') as f:
                f.write(f"{next_cluster}\t{cluster_sum}\n")
        else:
            break  # 没有更多列可以作为cluster

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py <input_file> <output_file> <num_clusters>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    num_clusters = int(sys.argv[3])

    process_data(input_file, output_file, num_clusters)
