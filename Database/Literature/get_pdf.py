# -*- coding: utf-8 -*-
# @Author: jwli.
# @Date  : 2024/6/11
# version: Python 3.10.0
import requests
from bs4 import BeautifulSoup
import os
import urllib3
import time
import random
from urllib.parse import urljoin

# 忽略InsecureRequestWarning警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SciHubDownloader:
    def __init__(self):
        # 多个可用的Sci-Hub域名
        self.scihub_domains = [
            "https://sci-hub.ren/",
            "https://sci-hub.se/",
            "https://sci-hub.st/",
            "https://sci-hub.ru/",
            "https://sci-hub.hkvisa.net/"
        ]
        self.current_domain_index = 0
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_current_domain(self):
        return self.scihub_domains[self.current_domain_index]

    def switch_domain(self):
        """切换到下一个域名"""
        self.current_domain_index = (self.current_domain_index + 1) % len(self.scihub_domains)
        print(f"切换到域名: {self.get_current_domain()}")

    def try_unpaywall(self, doi):
        """尝试通过Unpaywall获取PDF链接"""
        try:
            # Unpaywall API端点
            unpaywall_url = f"https://api.unpaywall.org/v2/{doi}?email=1369176312@qq.com"

            print(f"尝试Unpaywall API: {doi}")

            response = self.session.get(unpaywall_url, timeout=15, verify=False)

            if response.status_code == 200:
                data = response.json()

                # 检查是否有最佳开放获取位置
                if data.get('best_oa_location'):
                    oa_location = data['best_oa_location']

                    # 优先使用PDF链接
                    pdf_url = oa_location.get('url_for_pdf')
                    if pdf_url:
                        print(f"Unpaywall找到PDF链接: {pdf_url}")
                        return pdf_url

                    # 如果没有PDF链接，使用普通URL
                    pdf_url = oa_location.get('url')
                    if pdf_url and self.is_likely_pdf_url(pdf_url):
                        print(f"Unpaywall找到可能包含PDF的链接: {pdf_url}")
                        return pdf_url

                # 检查所有开放获取位置
                for oa_location in data.get('oa_locations', []):
                    pdf_url = oa_location.get('url_for_pdf') or oa_location.get('url')
                    if pdf_url and self.is_likely_pdf_url(pdf_url):
                        print(f"Unpaywall找到PDF链接: {pdf_url}")
                        return pdf_url

                print("Unpaywall未找到可用的PDF链接")
                return None

            else:
                print(f"Unpaywall API请求失败，状态码: {response.status_code}")
                return None

        except Exception as e:
            print(f"Unpaywall API错误: {e}")
            return None

    def is_likely_pdf_url(self, url):
        """判断URL是否可能是PDF链接"""
        return any(ext in url.lower() for ext in ['.pdf', '/pdf', 'download', 'article', 'content'])

    def download_pdf_from_url(self, pdf_url, output_path):
        """从URL下载PDF文件"""
        try:
            response = self.session.get(pdf_url, stream=True, timeout=60, verify=False)

            if response.status_code == 200:
                # 检查内容类型
                content_type = response.headers.get('content-type', '').lower()
                if 'pdf' in content_type or pdf_url.lower().endswith('.pdf'):
                    with open(output_path, 'wb') as file:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                file.write(chunk)

                    # 验证文件大小
                    file_size = os.path.getsize(output_path)
                    if file_size > 1024:  # 大于1KB
                        print(f"PDF下载成功，文件大小: {file_size} 字节")
                        return True
                    else:
                        os.remove(output_path)
                        print("下载的文件过小，可能不是有效的PDF")
                        return False
                else:
                    print(f"URL返回的内容不是PDF，Content-Type: {content_type}")
                    return False
            else:
                print(f"PDF下载失败，状态码: {response.status_code}")
                return False

        except Exception as e:
            print(f"PDF下载错误: {e}")
            return False

    def extract_pdf_url(self, soup, base_url):
        """从页面中提取PDF URL"""
        # 方法1: 查找iframe
        iframe = soup.find('iframe')
        if iframe and iframe.get('src'):
            pdf_url = iframe['src']
            if not pdf_url.startswith('http'):
                pdf_url = urljoin(base_url, pdf_url)
            return pdf_url

        # 方法2: 查找PDF链接按钮
        pdf_buttons = soup.find_all('button', onclick=True)
        for button in pdf_buttons:
            onclick = button.get('onclick', '')
            if 'location.href' in onclick:
                # 提取URL
                start = onclick.find("'") + 1
                end = onclick.find("'", start)
                if start > 0 and end > start:
                    pdf_url = onclick[start:end]
                    if not pdf_url.startswith('http'):
                        pdf_url = urljoin(base_url, pdf_url)
                    return pdf_url

        # 方法3: 查找PDF链接
        pdf_links = soup.find_all('a', href=True)
        for link in pdf_links:
            href = link['href']
            if href.endswith('.pdf') or 'pdf' in href.lower():
                if not href.startswith('http'):
                    href = urljoin(base_url, href)
                return href

        return None

    def download_paper(self, doi, output_dir, max_retries=3):
        """下载论文"""
        filename = f"{doi.replace('/', '_')}.pdf"
        output_path = os.path.join(output_dir, filename)

        # 如果文件已存在，跳过下载
        if os.path.exists(output_path):
            print(f"文件已存在: {filename}")
            return True

        print(f"\n开始下载: {doi}")

        # 策略1: 首先尝试Unpaywall（合法途径）
        print("策略1: 尝试Unpaywall...")
        pdf_url = self.try_unpaywall(doi)
        if pdf_url and self.download_pdf_from_url(pdf_url, output_path):
            print(f"✓ 通过Unpaywall下载成功")
            return True

        # 策略2: 如果Unpaywall失败，使用Sci-Hub
        print("策略2: 尝试Sci-Hub...")
        for retry in range(max_retries):
            try:
                base_url = self.get_current_domain()
                url = base_url + doi

                print(f"尝试下载 DOI: {doi} (尝试 {retry + 1}/{max_retries})")

                # 添加随机延迟避免被屏蔽
                time.sleep(random.uniform(1, 3))

                response = self.session.get(url, verify=False, timeout=30)

                if response.status_code == 403:
                    print(f"域名 {base_url} 被屏蔽，尝试切换域名")
                    self.switch_domain()
                    continue
                elif response.status_code != 200:
                    print(f"访问失败，状态码: {response.status_code}")
                    continue

                soup = BeautifulSoup(response.content, 'html.parser')

                # 提取PDF URL
                pdf_url = self.extract_pdf_url(soup, base_url)

                if not pdf_url:
                    print(f"未找到PDF链接: {doi}")
                    # 保存HTML页面用于调试
                    debug_path = os.path.join(output_dir, f"{doi.replace('/', '_')}_debug.html")
                    with open(debug_path, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"已保存调试页面: {debug_path}")
                    continue

                print(f"找到PDF链接: {pdf_url}")

                # 下载PDF
                if self.download_pdf_from_url(pdf_url, output_path):
                    print(f"✓ 通过Sci-Hub下载成功")
                    return True
                else:
                    print(f"PDF下载失败")

            except requests.exceptions.RequestException as e:
                print(f"网络错误: {e}")
                time.sleep(2)  # 网络错误后等待

            except Exception as e:
                print(f"未知错误: {e}")
                break

        print(f"下载失败: {doi}")
        return False

def batch_download(doi_file, output_dir):
    """批量下载"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    downloader = SciHubDownloader()

    with open(doi_file, 'r', encoding='utf-8') as file:
        dois = [line.strip() for line in file if line.strip()]

    print(f"找到 {len(dois)} 个DOI需要下载")

    success_count = 0
    for i, doi in enumerate(dois, 1):
        print(f"\n[{i}/{len(dois)}] 处理DOI: {doi}")

        if downloader.download_paper(doi, output_dir):
            success_count += 1

        # 处理完一个DOI后稍作休息
        if i < len(dois):
            sleep_time = random.uniform(2, 5)
            print(f"等待 {sleep_time:.1f} 秒后继续...")
            time.sleep(sleep_time)

    print(f"\n下载完成! 成功: {success_count}/{len(dois)}")
    print(f"成功率: {success_count/len(dois)*100:.1f}%")

if __name__ == "__main__":
    doi_file = "doi.txt"
    output_dir = "downloaded_papers"

    # 检查DOI文件是否存在
    if not os.path.exists(doi_file):
        print(f"错误: DOI文件 '{doi_file}' 不存在")
        print("请创建doi.txt文件，每行一个DOI")
    else:
        batch_download(doi_file, output_dir)
