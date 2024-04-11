"""
@Author: jwli
Date: 2024-4-11
Location: Huazhong Agricultural University
Description: This script reads SRA numbers from a text file, retrieves Biosample information from the NCBI website,
and writes the information to an output file, sra_info.txt, with each piece of information separated by tabs.
"""
import sys
import requests
import re
from bs4 import BeautifulSoup
import time
from retrying import retry

def read_sra_numbers_from_txt(txt_filename):
    with open(txt_filename, 'r') as file:
        sra_numbers = file.read().splitlines()
    return sra_numbers

@retry()
def extract_biosample_info(biosample_url, sra, file):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
    }
    response = requests.get(biosample_url, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')

    def get_value_by_label(soup, label):
        if label.lower() == "description":
            description_dt = soup.find("dt", string=lambda text: text and text.lower() == label.lower())
            if description_dt:
                description_dd = description_dt.find_next("dd")
                if description_dd:
                    return description_dd.text.strip()
            return "-"
        else:
            th = soup.find("th", string=lambda text: text and text.lower() == label.lower())
            if th and th.find_next_sibling("td"):
                return th.find_next_sibling("td").text.strip()
            else:
                return "-"

    # 确定需要提取的信息
    values = [
        sra,
        re.search(r'SAMN\d+', biosample_url).group() if re.search(r'SAMN\d+', biosample_url) else "Unknown SRA",
        get_value_by_label(soup, "cultivar"),
        get_value_by_label(soup, "tissue"),
        get_value_by_label(soup, "geographic location"),
        get_value_by_label(soup, "sample type"),
        get_value_by_label(soup, "label"),
        get_value_by_label(soup, "development stage"),
        get_value_by_label(soup, "habitat"),
        get_value_by_label(soup, "Description")
    ]

    # 写入到文件
    file.write('\t'.join(values) + '\n')

def get_biosample_information(sra_numbers, output_file):
    with open(output_file, 'w') as file:
        # 写入header
        headers = ["SRA", "BioSample SRA", "Cultivar", "Tissue", "Geographic Location", "Sample Type", "Label", "Development Stage", "Habitat", "Description"]
        file.write('\t'.join(headers) + '\n')

        for srr in sra_numbers:
            url = f'https://www.ncbi.nlm.nih.gov/sra/?term={srr}'
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'lxml')
            sample_link_selector = '#ResultView > div:nth-child(4) > span > div > a:nth-child(1)'
            sample = soup.select(sample_link_selector)
            if not sample:
                sample_link_selector = '#ResultView > div:nth-child(3) > span > div > a:nth-child(1)'
                sample = soup.select(sample_link_selector)
            if sample:
                result1 = str(sample[0])
                link = re.findall('/\w+\/\w+', result1)
                if link:
                    biosample_url = f'https://www.ncbi.nlm.nih.gov{link[0]}'
                    extract_biosample_info(biosample_url, srr, file)
                    time.sleep(2)

if __name__ == "__main__":
    txt_filename = sys.argv[1]
    output_filename = sys.argv[2]
    sra_numbers = read_sra_numbers_from_txt(txt_filename)
    get_biosample_information(sra_numbers, output_filename)
