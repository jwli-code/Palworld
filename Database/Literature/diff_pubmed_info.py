# @Author: jwli.
# @Date  : 2024/04/16
import pandas as pd
import sys

def filter_excel(input_excel, dois_file, output_excel):
    # 读取Excel表格和DOI号文件
    excel_data = pd.read_excel(input_excel)
    with open(dois_file, 'r',encoding='gbk',errors='ignore') as f:
        # 跳过空行并去除行末的换行符
        dois = {line.strip() for line in f if line.strip()}

    # 过滤Excel表格中不在DOI号文件中的行
    filtered_data = excel_data[~excel_data['DOI'].isin(dois)]

    # 将过滤后的数据写入新的Excel文件
    filtered_data.to_excel(output_excel, index=False)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py <input_excel> <dois_file> <output_excel>")
        sys.exit(1)

    input_excel = sys.argv[1]
    dois_file = sys.argv[2]
    output_excel = sys.argv[3]

    filter_excel(input_excel, dois_file, output_excel)
