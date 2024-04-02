import sys
import pandas as pd

def process_data(input_file, threshold, output_file):
    # 读取数据
    data = pd.read_csv(input_file, sep='\t', index_col=0)

    # 将数据转换为浮点数格式
    data = data.apply(pd.to_numeric, errors='coerce')

    # 应用转换，大于等于阈值的设置为1，小于阈值的设置为0
    data = data.applymap(lambda x: 1 if x >= threshold else 0)

    # 保存数据
    data.to_csv(output_file, sep='\t')

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py <input_file> <threshold> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    threshold = float(sys.argv[2])
    output_file = sys.argv[3]

    process_data(input_file, threshold, output_file)
