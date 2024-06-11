# -*- coding: utf-8 -*- 
# @Author: jwli.
# @Date  : 2024/6/11
# version: Python 3.10.0
import requests
from bs4 import BeautifulSoup
import os
import urllib3

# 忽略InsecureRequestWarning警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download_paper(doi, output_dir):
    base_url = "https://sci-hub.ren/"
    url = base_url + doi
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code != 200:
        print(f"Failed to access Sci-Hub for DOI {doi} with status code {response.status_code}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    iframe = soup.find('iframe')

    if not iframe or 'src' not in iframe.attrs:
        print(f"PDF not found for DOI {doi}, looking for alternative download method.")

        pdf_link_tag = soup.find('a', {'href': True})
        if pdf_link_tag:
            pdf_url = pdf_link_tag['href']
            if not pdf_url.startswith('http'):
                pdf_url = "https:" + pdf_url

            pdf_response = requests.get(pdf_url, headers=headers, verify=False)

            if pdf_response.status_code == 200:
                output_path = os.path.join(output_dir, f"{doi.replace('/', '_')}.pdf")
                with open(output_path, 'wb') as file:
                    file.write(pdf_response.content)
                print(f"Downloaded PDF for DOI {doi}")
            else:
                print(f"Failed to download PDF for DOI {doi} with status code {pdf_response.status_code}")
        else:
            print(f"No alternative download method found for DOI {doi}")
        return

    pdf_url = iframe['src']

    if not pdf_url.startswith('http'):
        pdf_url = "https:" + pdf_url

    pdf_response = requests.get(pdf_url, headers=headers, verify=False)

    if pdf_response.status_code == 200:
        output_path = os.path.join(output_dir, f"{doi.replace('/', '_')}.pdf")
        with open(output_path, 'wb') as file:
            file.write(pdf_response.content)
        print(f"Downloaded PDF for DOI {doi}")
    else:
        print(f"Failed to download PDF for DOI {doi} with status code {pdf_response.status_code}")

def batch_download(doi_file, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(doi_file, 'r') as file:
        dois = file.readlines()

    for doi in dois:
        doi = doi.strip()
        if doi:
            download_paper(doi, output_dir)

if __name__ == "__main__":
    doi_file = "doi.txt"
    output_dir = "downloaded_papers"
    batch_download(doi_file, output_dir)
