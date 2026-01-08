#!/usr/bin/env python3
"""
author: jwli
data: 2026.1.8
统一文献下载器 - 多策略批量下载工具（增强版）

策略优先级：
1. 期刊特定下载 (MDPI/Frontier/NAR/PLOS等)
2. 通用下载 (Sci-Hub/Unpaywall/Library Genesis)
3. Wiley API
4. Elsevier API
5. Crossref/DOI.org 直接解析

使用方法：
    单个下载: python unified_downloader.py --doi 10.xxx/xxx
    批量下载: python unified_downloader.py --batch doi.txt
"""

__author__ = "综合工具"
__version__ = "2.0.0"

import requests
import argparse
import sys
import os
import time
import random
import json
import re
from urllib.parse import quote_plus, urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
import urllib3
from datetime import datetime

# 忽略InsecureRequestWarning警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class UnifiedDownloader:
    def __init__(self, output_dir="downloaded_papers"):
        """初始化下载器"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # 失败记录文件
        self.failed_file = os.path.join(output_dir, "failed_downloads.json")

        # API密钥配置
        self.wiley_api_key = "1ea17669-44fb-429e-9341-19e8258b3b75"
        self.elsevier_api_key = "bb01ca19ba1d3794da3e6063c15af77e"

        # 加载历史失败记录
        self.failed_dois = self.load_failed_dois()

        # 初始化session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def load_failed_dois(self):
        """加载失败的DOI记录"""
        if os.path.exists(self.failed_file):
            try:
                with open(self.failed_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_failed_dois(self):
        """保存失败的DOI记录"""
        with open(self.failed_file, 'w', encoding='utf-8') as f:
            json.dump(self.failed_dois, f, indent=2, ensure_ascii=False)

    def mark_as_failed(self, doi, reason, strategy):
        """标记DOI下载失败"""
        if doi not in self.failed_dois:
            self.failed_dois[doi] = []

        self.failed_dois[doi].append({
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "strategy": strategy
        })
        self.save_failed_dois()

    def download_by_strategies(self, doi, max_retries=2):
        """使用多种策略下载文献"""
        filename = f"{doi.replace('/', '_').replace(':', '_')}.pdf"
        output_path = os.path.join(self.output_dir, filename)

        # 检查文件是否已存在
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
            print(f"✓ 文件已存在: {filename}")
            return True, "already_exists"

        strategies = [
            ("Sci-Hub优先", lambda d: self._download_scihub_enhanced(d, output_path)),
            ("期刊特定下载", lambda d: self._download_journal_specific(d, output_path)),
            ("Library Genesis", lambda d: self._download_libgen(d, output_path)),
            ("通用下载增强", lambda d: self._download_general_enhanced(d, output_path)),
            ("Wiley API", lambda d: self._download_wiley(d, output_path)),
            ("Elsevier API", lambda d: self._download_elsevier(d, output_path)),
            ("Crossref解析", lambda d: self._download_via_crossref(d, output_path)),
        ]

        for strategy_name, download_func in strategies:
            print(f"\n[{doi}] 尝试策略: {strategy_name}")

            for retry in range(max_retries):
                try:
                    success, message = download_func(doi)
                    if success:
                        # 检查文件是否确实下载成功
                        if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                            print(f"✓ 通过{strategy_name}下载成功: {filename}")
                            return True, strategy_name

                    print(f"✗ {strategy_name} 失败: {message}")

                except Exception as e:
                    print(f"✗ {strategy_name} 异常: {str(e)}")

                if retry < max_retries - 1:
                    time.sleep(random.uniform(1, 3))

            # 策略失败后稍作延迟
            time.sleep(random.uniform(0.5, 1.5))

        # 所有策略都失败
        error_msg = f"所有下载策略均失败: {doi}"
        self.mark_as_failed(doi, error_msg, "all_strategies")
        return False, error_msg

    def _download_journal_specific(self, doi, output_path):
        """针对特定期刊的下载方法"""
        try:
            # 首先尝试直接根据DOI判断期刊类型（避免403错误）
            doi_lower = doi.lower()

            # MDPI DOI通常以10.3390开头
            if doi_lower.startswith('10.3390'):
                # 直接尝试MDPI下载，不依赖DOI页面
                result = self._download_mdpi_direct(doi, output_path)
                if result[0]:
                    return result
                # 如果直接方法失败，再尝试访问页面

            # 获取DOI的元数据，确定期刊
            doi_url = f"https://doi.org/{doi}"

            # 改进请求头，避免403
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
                'Referer': 'https://www.google.com/',
            }

            try:
                response = self.session.get(doi_url, headers=headers, allow_redirects=True, timeout=15, verify=False)
                final_url = response.url
                html_content = response.text if response.status_code == 200 else ""
            except:
                final_url = ""
                html_content = ""

            # 检测期刊类型并下载
            if 'mdpi.com' in final_url.lower() or doi_lower.startswith('10.3390'):
                if html_content:
                    result = self._download_mdpi(doi, final_url, html_content, output_path)
                    if result[0]:
                        return result
                # 即使无法访问页面，也尝试直接下载
                return self._download_mdpi_direct(doi, output_path)
            elif 'frontiersin.org' in final_url.lower() or doi_lower.startswith('10.3389'):
                if html_content:
                    return self._download_frontier(doi, final_url, html_content, output_path)
                return self._download_frontier_direct(doi, output_path)
            elif 'academic.oup.com' in final_url.lower() or 'nar.oxfordjournals.org' in final_url.lower():
                if html_content:
                    return self._download_oup_nar(doi, final_url, html_content, output_path)
            elif 'plos.org' in final_url.lower():
                if html_content:
                    return self._download_plos(doi, final_url, html_content, output_path)
            elif 'springer.com' in final_url.lower() or 'springeropen.com' in final_url.lower():
                if html_content:
                    return self._download_springer(doi, final_url, html_content, output_path)
            elif 'nature.com' in final_url.lower():
                if html_content:
                    return self._download_nature(doi, final_url, html_content, output_path)
            elif 'bmc.com' in final_url.lower() or 'biomedcentral.com' in final_url.lower():
                if html_content:
                    return self._download_bmc(doi, final_url, html_content, output_path)
            elif 'ieee.org' in final_url.lower():
                if html_content:
                    return self._download_ieee(doi, final_url, html_content, output_path)
            elif 'acs.org' in final_url.lower():
                if html_content:
                    return self._download_acs(doi, final_url, html_content, output_path)

            # 如果无法访问页面，返回错误
            if not html_content:
                return False, f"无法访问DOI页面或页面为空"

            # 尝试从页面中提取PDF链接（通用方法）
            return self._extract_pdf_from_page(html_content, final_url, output_path)

        except Exception as e:
            return False, f"journal_specific_error: {str(e)}"

    def _download_mdpi_direct(self, doi, output_path):
        """直接下载MDPI文章（不依赖页面访问）"""
        try:
            # 方法1: 通过DOI重定向获取文章URL，然后构造PDF URL
            # 这是最可靠的方法
            try:
                doi_url = f"https://doi.org/{doi}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://www.google.com/',
                }

                # 尝试多次，使用不同的方法
                for attempt in range(2):
                    try:
                        response = self.session.get(doi_url, headers=headers, allow_redirects=True, timeout=15, verify=False)
                        if response.status_code == 200:
                            article_url = response.url
                            # 从文章URL构造PDF URL
                            if 'mdpi.com' in article_url.lower():
                                # 尝试多种PDF URL格式
                                pdf_urls = []

                                if '/article/' in article_url:
                                    pdf_urls.append(article_url.replace('/article/', '/pdf/'))

                                # 尝试其他可能的格式
                                match = re.search(r'(https?://[^/]+/)([^/]+)/([^/]+)/([^/]+)/([^/]+)', article_url)
                                if match:
                                    base = match.group(1)
                                    pdf_urls.append(f"{base}{match.group(2)}/{match.group(3)}/{match.group(4)}/{match.group(5)}/pdf")

                                for pdf_url in pdf_urls:
                                    if self._download_pdf_file(pdf_url, output_path):
                                        return True, "mdpi_doi_redirect"
                        elif response.status_code == 403:
                            # 403错误，尝试使用不同的User-Agent
                            headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                            time.sleep(1)
                            continue
                    except requests.exceptions.Timeout:
                        time.sleep(2)
                        continue
                    except:
                        break
            except Exception as e:
                pass

            # 方法2: 通过Crossref API获取文章URL
            try:
                crossref_url = f"https://api.crossref.org/works/{doi}"
                response = self.session.get(crossref_url, timeout=10, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    if 'message' in data:
                        # 查找MDPI的URL
                        links = data['message'].get('link', [])
                        for link in links:
                            url = link.get('URL', '')
                            if 'mdpi.com' in url.lower():
                                # 尝试构造PDF URL
                                if '/article/' in url:
                                    pdf_url = url.replace('/article/', '/pdf/')
                                    if self._download_pdf_file(pdf_url, output_path):
                                        return True, "mdpi_crossref"
            except:
                pass

            # 方法3: 尝试直接构造PDF URL（基于DOI格式）
            # DOI格式: 10.3390/ijms26125780
            # 文章ID可能是: 26/12/5780 (卷/期/文章号)
            parts = doi.split('/')
            if len(parts) == 2 and parts[0] == '10.3390':
                suffix = parts[1].lower()
                # 提取数字部分
                numbers = re.findall(r'\d+', suffix)
                if len(numbers) >= 1:
                    article_num = numbers[0]
                    # 尝试不同的分割方式
                    if len(article_num) >= 6:
                        # 可能是 26/12/5780 格式
                        volume = article_num[:2]
                        issue = article_num[2:4]
                        article = article_num[4:]

                        # 尝试不同的期刊代码映射
                        journal_codes = {
                            'ijms': '1422-0067',
                            'molecules': '1420-3049',
                            'polymers': '2073-4360',
                            'nanomaterials': '2079-4991',
                            'cancers': '2072-6694',
                        }

                        # 提取期刊代码
                        journal_code = re.match(r'([a-z]+)', suffix).group(1) if re.match(r'([a-z]+)', suffix) else None

                        if journal_code and journal_code in journal_codes:
                            issn = journal_codes[journal_code]
                            pdf_url = f"https://www.mdpi.com/{issn}/{volume}/{issue}/{article}/pdf"
                            if self._download_pdf_file(pdf_url, output_path):
                                return True, "mdpi_constructed_from_doi"

            return False, "mdpi_direct_no_pdf"
        except Exception as e:
            return False, f"mdpi_direct_error: {str(e)}"

    def _download_mdpi(self, doi, url, html, output_path):
        """下载MDPI期刊文章（从页面提取）"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 方法1: 查找PDF下载按钮/链接
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf|download.*pdf|/pdf/', re.I))
            for link in pdf_links:
                pdf_url = link.get('href', '')
                if pdf_url:
                    if not pdf_url.startswith('http'):
                        pdf_url = urljoin(url, pdf_url)
                    if self._download_pdf_file(pdf_url, output_path):
                        return True, "mdpi_direct"

            # 方法2: 查找iframe中的PDF
            iframes = soup.find_all('iframe')
            for iframe in iframes:
                src = iframe.get('src', '')
                if 'pdf' in src.lower():
                    if not src.startswith('http'):
                        src = urljoin(url, src)
                    if self._download_pdf_file(src, output_path):
                        return True, "mdpi_iframe"

            # 方法3: 构造MDPI PDF URL
            # MDPI的PDF通常格式为: https://www.mdpi.com/xxx/xxx/xxx/pdf
            if '/article/' in url:
                pdf_url = url.replace('/article/', '/pdf/')
                if self._download_pdf_file(pdf_url, output_path):
                    return True, "mdpi_constructed"

            return False, "mdpi_no_pdf_found"
        except Exception as e:
            return False, f"mdpi_error: {str(e)}"

    def _download_frontier_direct(self, doi, output_path):
        """直接下载Frontier文章（不依赖页面访问）"""
        try:
            # 通过DOI获取文章URL
            doi_url = f"https://doi.org/{doi}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml',
            }
            try:
                response = self.session.get(doi_url, headers=headers, allow_redirects=True, timeout=10, verify=False)
                if response.status_code == 200:
                    article_url = response.url
                    if 'frontiersin.org' in article_url:
                        # 构造PDF URL
                        match = re.search(r'/articles/([^/]+)', article_url)
                        if match:
                            article_id = match.group(1)
                            pdf_url = f"https://www.frontiersin.org/articles/{article_id}/pdf"
                            if self._download_pdf_file(pdf_url, output_path):
                                return True, "frontier_direct_constructed"
            except:
                pass

            return False, "frontier_direct_no_pdf"
        except Exception as e:
            return False, f"frontier_direct_error: {str(e)}"

    def _download_frontier(self, doi, url, html, output_path):
        """下载Frontier期刊文章（从页面提取）"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Frontier的PDF通常在特定位置
            pdf_selectors = [
                'a[href*=".pdf"]',
                'a[href*="/pdf/"]',
                'a[data-track-action="download pdf"]',
                '.article-pdf-link',
                '#pdf-download'
            ]

            for selector in pdf_selectors:
                links = soup.select(selector)
                for link in links:
                    pdf_url = link.get('href', '')
                    if pdf_url:
                        if not pdf_url.startswith('http'):
                            pdf_url = urljoin(url, pdf_url)
                        if self._download_pdf_file(pdf_url, output_path):
                            return True, "frontier_direct"

            # 尝试构造PDF URL
            # Frontier格式: https://www.frontiersin.org/articles/xxx/full -> xxx/pdf
            match = re.search(r'/articles/([^/]+)', url)
            if match:
                article_id = match.group(1)
                pdf_url = f"https://www.frontiersin.org/articles/{article_id}/pdf"
                if self._download_pdf_file(pdf_url, output_path):
                    return True, "frontier_constructed"

            return False, "frontier_no_pdf_found"
        except Exception as e:
            return False, f"frontier_error: {str(e)}"

    def _download_oup_nar(self, doi, url, html, output_path):
        """下载Oxford University Press (NAR等)文章"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # OUP的PDF链接通常在特定位置
            pdf_selectors = [
                'a[href*=".pdf"]',
                'a[data-article-id]',
                '.article-pdf',
                '.pdf-link',
                'a[title*="PDF"]'
            ]

            for selector in pdf_selectors:
                links = soup.select(selector)
                for link in links:
                    pdf_url = link.get('href', '')
                    if pdf_url:
                        if not pdf_url.startswith('http'):
                            pdf_url = urljoin(url, pdf_url)
                        # OUP可能需要添加参数
                        if '?' not in pdf_url:
                            pdf_url += '?download=true'
                        if self._download_pdf_file(pdf_url, output_path):
                            return True, "oup_direct"

            # 尝试构造PDF URL
            # OUP格式: https://academic.oup.com/nar/article/xxx/xxx/xxx/xxx -> /pdf/xxx/xxx/xxx/xxx.pdf
            match = re.search(r'/article/(\d+)/(\d+)/(\d+)/(\d+)/(\d+)', url)
            if match:
                pdf_url = f"https://academic.oup.com/nar/article-pdf/{match.group(1)}/{match.group(2)}/{match.group(3)}/{match.group(4)}/{match.group(5)}.pdf"
                if self._download_pdf_file(pdf_url, output_path):
                    return True, "oup_constructed"

            return False, "oup_no_pdf_found"
        except Exception as e:
            return False, f"oup_error: {str(e)}"

    def _download_plos(self, doi, url, html, output_path):
        """下载PLOS文章"""
        try:
            # PLOS通常是开放获取，PDF链接明确
            pdf_url = url.replace('/article?id=', '/article/file?id=') + '&type=printable'
            if not pdf_url.endswith('.pdf'):
                pdf_url = pdf_url.replace('/article/file?id=', '/article/asset/') + '.pdf'

            if self._download_pdf_file(pdf_url, output_path):
                return True, "plos_direct"

            # 备用方法：从页面提取
            soup = BeautifulSoup(html, 'html.parser')
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.I))
            for link in pdf_links:
                pdf_url = link.get('href', '')
                if pdf_url and not pdf_url.startswith('http'):
                    pdf_url = urljoin(url, pdf_url)
                if self._download_pdf_file(pdf_url, output_path):
                        return True, "plos_extracted"

            return False, "plos_no_pdf_found"
        except Exception as e:
            return False, f"plos_error: {str(e)}"

    def _download_springer(self, doi, url, html, output_path):
        """下载Springer文章"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Springer PDF链接
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf|/pdf/', re.I))
            for link in pdf_links:
                pdf_url = link.get('href', '')
                if pdf_url:
                    if not pdf_url.startswith('http'):
                        pdf_url = urljoin(url, pdf_url)
                    if self._download_pdf_file(pdf_url, output_path):
                        return True, "springer_direct"

            # 构造PDF URL
            if '/article/' in url:
                pdf_url = url + '.pdf'
                if self._download_pdf_file(pdf_url, output_path):
                    return True, "springer_constructed"

            return False, "springer_no_pdf_found"
        except Exception as e:
            return False, f"springer_error: {str(e)}"

    def _download_nature(self, doi, url, html, output_path):
        """下载Nature文章"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Nature PDF链接
            pdf_selectors = [
                'a[data-track-action="download pdf"]',
                'a[href*=".pdf"]',
                '.c-pdf-download'
            ]

            for selector in pdf_selectors:
                links = soup.select(selector)
                for link in links:
                    pdf_url = link.get('href', '')
                    if pdf_url:
                        if not pdf_url.startswith('http'):
                            pdf_url = urljoin(url, pdf_url)
                        if self._download_pdf_file(pdf_url, output_path):
                            return True, "nature_direct"

            return False, "nature_no_pdf_found"
        except Exception as e:
            return False, f"nature_error: {str(e)}"

    def _download_bmc(self, doi, url, html, output_path):
        """下载BMC文章"""
        try:
            # BMC通常是开放获取
            pdf_url = url + '.pdf'
            if self._download_pdf_file(pdf_url, output_path):
                return True, "bmc_direct"

            soup = BeautifulSoup(html, 'html.parser')
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.I))
            for link in pdf_links:
                pdf_url = link.get('href', '')
                if pdf_url and not pdf_url.startswith('http'):
                    pdf_url = urljoin(url, pdf_url)
                if self._download_pdf_file(pdf_url, output_path):
                    return True, "bmc_extracted"

            return False, "bmc_no_pdf_found"
        except Exception as e:
            return False, f"bmc_error: {str(e)}"

    def _download_ieee(self, doi, url, html, output_path):
        """下载IEEE文章"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # IEEE PDF链接
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf|download', re.I))
            for link in pdf_links:
                pdf_url = link.get('href', '')
                if pdf_url:
                    if not pdf_url.startswith('http'):
                        pdf_url = urljoin(url, pdf_url)
                    if self._download_pdf_file(pdf_url, output_path):
                        return True, "ieee_direct"

            return False, "ieee_no_pdf_found"
        except Exception as e:
            return False, f"ieee_error: {str(e)}"

    def _download_acs(self, doi, url, html, output_path):
        """下载ACS文章"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # ACS PDF链接
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf|pdf.*download', re.I))
            for link in pdf_links:
                pdf_url = link.get('href', '')
                if pdf_url:
                    if not pdf_url.startswith('http'):
                        pdf_url = urljoin(url, pdf_url)
                    if self._download_pdf_file(pdf_url, output_path):
                        return True, "acs_direct"

            return False, "acs_no_pdf_found"
        except Exception as e:
            return False, f"acs_error: {str(e)}"

    def _extract_pdf_from_page(self, html, base_url, output_path):
        """从页面中提取PDF链接（通用方法）"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 查找所有可能的PDF链接
            pdf_patterns = [
                r'\.pdf',
                r'/pdf/',
                r'pdf.*download',
                r'download.*pdf'
            ]

            for pattern in pdf_patterns:
                links = soup.find_all('a', href=re.compile(pattern, re.I))
                for link in links:
                    pdf_url = link.get('href', '')
                    if pdf_url:
                        if not pdf_url.startswith('http'):
                            pdf_url = urljoin(base_url, pdf_url)
                        if self._download_pdf_file(pdf_url, output_path):
                            return True, "extracted_from_page"

            # 查找iframe
            iframes = soup.find_all('iframe')
            for iframe in iframes:
                src = iframe.get('src', '')
                if 'pdf' in src.lower():
                    if not src.startswith('http'):
                        src = urljoin(base_url, src)
                    if self._download_pdf_file(src, output_path):
                        return True, "extracted_from_iframe"

            return False, "no_pdf_in_page"
        except Exception as e:
            return False, f"extract_error: {str(e)}"

    def _download_pdf_file(self, pdf_url, output_path):
        """下载PDF文件"""
        try:
            # 改进的请求头，避免被拒绝
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/pdf,application/octet-stream,*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://www.google.com/',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
            }

            # 如果是MDPI，添加特定的Referer
            if 'mdpi.com' in pdf_url.lower():
                headers['Referer'] = pdf_url.replace('/pdf/', '/article/')

            response = self.session.get(pdf_url, headers=headers, stream=True, timeout=30, verify=False, allow_redirects=True)

            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                # 更宽松的内容类型检查
                if any(x in content_type for x in ['pdf', 'octet-stream', 'binary']) or not content_type:
                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    # 验证文件
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                        # 简单验证是否为PDF（检查文件头）
                        try:
                            with open(output_path, 'rb') as f:
                                header = f.read(4)
                                if header == b'%PDF':
                                    return True
                                else:
                                    # 如果不是PDF，删除文件
                                    os.remove(output_path)
                                    return False
                        except:
                            # 如果读取失败，但文件大小合理，也认为成功
                            if os.path.getsize(output_path) > 5000:
                                return True
                            os.remove(output_path)
                            return False
                    return False
            elif response.status_code == 403:
                # 403错误，尝试不同的User-Agent
                headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                response = self.session.get(pdf_url, headers=headers, stream=True, timeout=30, verify=False, allow_redirects=True)
                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                        with open(output_path, 'rb') as f:
                            if f.read(4) == b'%PDF':
                                return True
                        os.remove(output_path)
            return False
        except Exception as e:
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            return False

    def _download_scihub_enhanced(self, doi, output_path):
        """增强的Sci-Hub下载方法（优先策略）"""
        try:
            # 更多Sci-Hub域名（定期更新）
            scihub_domains = [
                "https://sci-hub.se/",
                "https://sci-hub.st/",
                "https://sci-hub.ru/",
                "https://sci-hub.ren/",
                "https://sci-hub.wf/",
                "https://sci-hub.hkvisa.net/",
                "https://sci-hub.shop/",
                "https://sci-hub.ee/",
            ]

            for domain in scihub_domains:
                try:
                    url = domain + doi
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Referer': 'https://www.google.com/',
                    }

                    response = self.session.get(url, headers=headers, timeout=25, verify=False, allow_redirects=True)

                    if response.status_code == 403 or response.status_code == 404:
                        continue

                    if response.status_code != 200:
                        continue

                    soup = BeautifulSoup(response.content, 'html.parser')

                    # 改进的PDF URL提取
                    pdf_url = self._extract_pdf_url_enhanced(soup, domain, response.url)

                    if pdf_url:
                        if self._download_pdf_file(pdf_url, output_path):
                            return True, f"scihub_success_{domain.split('//')[1].split('/')[0]}"

                    # 如果直接提取失败，尝试查找按钮
                    download_button = soup.find('button', {'onclick': re.compile(r'location\.href|window\.open', re.I)})
                    if download_button:
                        onclick = download_button.get('onclick', '')
                        pdf_match = re.search(r"['\"]([^'\"]*\.pdf[^'\"]*)['\"]", onclick)
                        if pdf_match:
                            pdf_url = pdf_match.group(1)
                            if not pdf_url.startswith('http'):
                                pdf_url = urljoin(domain, pdf_url)
                            if self._download_pdf_file(pdf_url, output_path):
                                return True, f"scihub_button_{domain.split('//')[1].split('/')[0]}"

                except requests.exceptions.Timeout:
                    continue
                except Exception as e:
                    continue

            return False, "scihub_all_domains_failed"

        except Exception as e:
            return False, f"scihub_enhanced_error: {str(e)}"

    def _extract_pdf_url_enhanced(self, soup, base_url, page_url):
        """增强的PDF URL提取方法"""
        # 方法1: 查找iframe（最常见）
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            src = iframe.get('src', '')
            if src:
                if not src.startswith('http'):
                    src = urljoin(base_url, src)
                # 检查是否是PDF
                if '.pdf' in src.lower() or 'pdf' in src.lower():
                    return src

        # 方法2: 查找embed标签
        embeds = soup.find_all('embed')
        for embed in embeds:
            src = embed.get('src', '')
            if src:
                if not src.startswith('http'):
                    src = urljoin(base_url, src)
                if '.pdf' in src.lower():
                    return src

        # 方法3: 查找PDF下载链接
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf|download.*pdf|/pdf/', re.I))
        for link in pdf_links:
            href = link.get('href', '')
            if href:
                if not href.startswith('http'):
                    href = urljoin(base_url, href)
                return href

        # 方法4: 查找所有链接，检查是否指向PDF
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            if href and ('.pdf' in href.lower() or '/pdf/' in href.lower()):
                if not href.startswith('http'):
                    href = urljoin(base_url, href)
                return href

        # 方法5: 在页面源码中搜索PDF URL
        page_text = str(soup)
        pdf_patterns = [
            r'https?://[^\s"\'<>]+\.pdf',
            r'https?://[^\s"\'<>]+/pdf/[^\s"\'<>]+',
            r'location\.href\s*=\s*["\']([^"\']*\.pdf[^"\']*)["\']',
        ]

        for pattern in pdf_patterns:
            matches = re.findall(pattern, page_text, re.I)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match else ''
                if match and '.pdf' in match.lower():
                    if not match.startswith('http'):
                        match = urljoin(base_url, match)
                    return match

        return None

    def _download_libgen(self, doi, output_path):
        """通过Library Genesis下载"""
        try:
            # LibGen镜像列表
            libgen_mirrors = [
                "http://libgen.is",
                "http://libgen.rs",
                "http://libgen.st",
                "http://93.174.95.27",
            ]

            for mirror in libgen_mirrors:
                try:
                    # 搜索DOI
                    search_url = f"{mirror}/search.php"
                    params = {
                        'req': doi,
                        'lg_topic': 'libgen',
                        'open': '0',
                        'view': 'simple',
                        'res': '25',
                        'phrase': '1',
                        'column': 'def'
                    }

                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'text/html,application/xhtml+xml',
                    }

                    response = self.session.get(search_url, params=params, headers=headers, timeout=15, verify=False)

                    if response.status_code != 200:
                        continue

                    soup = BeautifulSoup(response.content, 'html.parser')

                    # 查找下载链接
                    # LibGen的下载链接通常在表格中
                    download_links = soup.find_all('a', href=re.compile(r'book/index\.php|ads\.php|\.php\?md5=', re.I))

                    for link in download_links[:3]:  # 只尝试前3个
                        href = link.get('href', '')
                        if href:
                            if not href.startswith('http'):
                                href = urljoin(mirror, href)

                            # 访问下载页面
                            try:
                                dl_response = self.session.get(href, headers=headers, timeout=15, verify=False, allow_redirects=True)
                                if dl_response.status_code == 200:
                                    dl_soup = BeautifulSoup(dl_response.content, 'html.parser')

                                    # 查找实际PDF下载链接
                                    pdf_links = dl_soup.find_all('a', href=re.compile(r'\.pdf|get\.php|\.php\?md5=', re.I))
                                    for pdf_link in pdf_links:
                                        pdf_href = pdf_link.get('href', '')
                                        if pdf_href:
                                            if not pdf_href.startswith('http'):
                                                pdf_href = urljoin(mirror, pdf_href)

                                            # 尝试下载
                                            if self._download_pdf_file(pdf_href, output_path):
                                                return True, f"libgen_success_{mirror.split('//')[1].split('/')[0]}"
                            except:
                                continue

                except:
                    continue

            return False, "libgen_no_results"
        except Exception as e:
            return False, f"libgen_error: {str(e)}"

    def _download_general_enhanced(self, doi, output_path):
        """增强的通用下载方法"""
        try:
            # 1. 尝试Unpaywall
            unpaywall_url = f"https://api.unpaywall.org/v2/{doi}?email=1369176312@qq.com"
            try:
                response = self.session.get(unpaywall_url, timeout=10, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('best_oa_location'):
                        oa_location = data['best_oa_location']
                        pdf_url = oa_location.get('url_for_pdf') or oa_location.get('url')
                        if pdf_url:
                            if self._download_pdf_file(pdf_url, output_path):
                                return True, "unpaywall_success"
            except:
                pass

            # 2. 尝试ResearchGate（如果文章是开放获取）
            try:
                rg_url = f"https://www.researchgate.net/search?q={quote_plus(doi)}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                }
                response = self.session.get(rg_url, headers=headers, timeout=10, verify=False)
                if response.status_code == 200:
                    # ResearchGate通常需要登录，但可以尝试
                    soup = BeautifulSoup(response.content, 'html.parser')
                    pdf_links = soup.find_all('a', href=re.compile(r'\.pdf|download', re.I))
                    for link in pdf_links[:2]:
                        pdf_url = link.get('href', '')
                        if pdf_url and not pdf_url.startswith('http'):
                            pdf_url = urljoin('https://www.researchgate.net', pdf_url)
                        if pdf_url and self._download_pdf_file(pdf_url, output_path):
                            return True, "researchgate_success"
            except:
                pass

            return False, "general_enhanced_failed"

        except Exception as e:
            return False, f"general_enhanced_error: {str(e)}"

    def _extract_pdf_url(self, soup, base_url):
        """从Sci-Hub页面提取PDF URL（保留向后兼容）"""
        return self._extract_pdf_url_enhanced(soup, base_url, base_url)

    def _download_via_crossref(self, doi, output_path):
        """通过Crossref API获取信息并尝试下载"""
        try:
            crossref_url = f"https://api.crossref.org/works/{doi}"
            response = self.session.get(crossref_url, timeout=10, verify=False)

            if response.status_code == 200:
                data = response.json()
                if 'message' in data:
                    # 尝试从返回的数据中获取PDF链接
                    links = data['message'].get('link', [])
                    for link in links:
                        if link.get('content-type') == 'application/pdf':
                            pdf_url = link.get('URL')
                            if pdf_url and self._download_pdf_file(pdf_url, output_path):
                                return True, "crossref_success"

            return False, "crossref_no_pdf"
        except Exception as e:
            return False, f"crossref_error: {str(e)}"

    def _download_wiley(self, doi, output_path):
        """通过Wiley API下载"""
        if not self.wiley_api_key:
            return False, "no_wiley_api_key"

        try:
            base_url = "https://api.wiley.com/onlinelibrary/tdm/v1/articles/"
            headers = {'Wiley-TDM-Client-Token': self.wiley_api_key}
            url = base_url + quote_plus(doi)

            response = self.session.get(url, headers=headers, stream=True, timeout=30)

            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                if os.path.getsize(output_path) > 1024:
                    return True, "wiley_success"
                else:
                    os.remove(output_path)
                    return False, "wiley_file_too_small"
            elif response.status_code == 403:
                return False, "wiley_unauthorized"
            elif response.status_code == 404:
                return False, "wiley_not_found"
            else:
                return False, f"wiley_http_{response.status_code}"

        except Exception as e:
            return False, f"wiley_error: {str(e)}"

    def _download_elsevier(self, doi, output_path):
        """通过Elsevier API下载"""
        if not self.elsevier_api_key:
            return False, "no_elsevier_api_key"

        try:
            base_url = f"https://api.elsevier.com/content/article/doi/{doi}"
            headers = {
                "X-ELS-APIKey": self.elsevier_api_key,
                "Accept": "application/json",
            }
            params = {
                "view": "FULL",
                "httpAccept": "application/pdf"
            }

            response = self.session.get(
                base_url,
                headers=headers,
                params=params,
                stream=True,
                timeout=30
            )

            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                if os.path.getsize(output_path) > 1024:
                    return True, "elsevier_success"
                else:
                    os.remove(output_path)
                    return False, "elsevier_file_too_small"
            else:
                return False, f"elsevier_http_{response.status_code}: {response.text[:100]}"

        except Exception as e:
            return False, f"elsevier_error: {str(e)}"

    def batch_download(self, doi_file, delay_between=2):
        """批量下载DOI列表"""
        if not os.path.exists(doi_file):
            print(f"错误: DOI文件 '{doi_file}' 不存在")
            return

        with open(doi_file, 'r', encoding='utf-8') as f:
            dois = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

        print(f"找到 {len(dois)} 个DOI需要下载")
        print(f"输出目录: {os.path.abspath(self.output_dir)}")

        success_count = 0
        for i, doi in enumerate(dois, 1):
            print(f"\n{'='*60}")
            print(f"[{i}/{len(dois)}] 处理DOI: {doi}")
            print(f"{'='*60}")

            success, _ = self.download_by_strategies(doi)
            if success:
                success_count += 1

            if i < len(dois):
                sleep_time = random.uniform(delay_between * 0.8, delay_between * 1.2)
                print(f"等待 {sleep_time:.1f} 秒后继续...")
                time.sleep(sleep_time)

        # 输出统计信息
        print(f"\n{'='*60}")
        print(f"下载完成!")
        print(f"成功: {success_count}/{len(dois)}")

        if len(dois) > 0:
            print(f"成功率: {success_count/len(dois)*100:.1f}%")

        if self.failed_dois:
            print(f"\n失败DOI列表已保存到: {self.failed_file}")
            print("\n失败的DOI:")
            for doi, failures in self.failed_dois.items():
                print(f"  - {doi}")
                for failure in failures[-1:]:
                    print(f"    原因: {failure['reason']}")
                    print(f"    策略: {failure['strategy']}")
                    print(f"    时间: {failure['timestamp']}")
        else:
            print(f"\n所有DOI下载成功！")


def main():
    parser = argparse.ArgumentParser(
        description="统一文献下载器 - 多策略批量下载工具（增强版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  单个DOI下载: python %(prog)s --doi 10.1111/pbi.13127
  批量下载:     python %(prog)s --batch doi.txt
  指定输出目录: python %(prog)s --batch doi.txt --output my_papers
  设置延迟:     python %(prog)s --batch doi.txt --delay 3

支持的期刊：
  - MDPI系列期刊
  - Frontier系列期刊
  - Oxford University Press (NAR等)
  - PLOS系列
  - Springer/Nature
  - BMC/BioMed Central
  - IEEE
  - ACS
  以及其他开放获取期刊

DOI文件格式 (每行一个DOI，支持#注释)：
  10.1111/pbi.13127
  10.1016/j.ijbiomac.2022.11.148
  # 这是一条注释
  10.1038/s41586-023-05800-7
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--doi", help="单个DOI下载")
    group.add_argument("--batch", help="批量下载，指定DOI列表文件路径")

    parser.add_argument("--output", "-o", default="downloaded_papers",
                       help="输出目录 (默认: downloaded_papers)")
    parser.add_argument("--delay", type=float, default=2.0,
                       help="批量下载时DOI之间的延迟秒数 (默认: 2)")
    parser.add_argument("--wiley-key", help="Wiley API密钥 (覆盖内置密钥)")
    parser.add_argument("--elsevier-key", help="Elsevier API密钥 (覆盖内置密钥)")
    parser.add_argument("--show-failed", action="store_true",
                       help="显示之前下载失败的DOI列表")

    args = parser.parse_args()

    downloader = UnifiedDownloader(output_dir=args.output)

    if args.wiley_key:
        downloader.wiley_api_key = args.wiley_key
    if args.elsevier_key:
        downloader.elsevier_api_key = args.elsevier_key

    if args.show_failed:
        if downloader.failed_dois:
            print("之前下载失败的DOI:")
            for doi, failures in downloader.failed_dois.items():
                print(f"\n- {doi}")
                for failure in failures:
                    print(f"  时间: {failure['timestamp']}")
                    print(f"  策略: {failure['strategy']}")
                    print(f"  原因: {failure['reason']}")
        else:
            print("没有失败的下载记录")
        return

    if args.doi:
        print(f"下载单个DOI: {args.doi}")
        success, result = downloader.download_by_strategies(args.doi)
        if success:
            print(f"\n✓ 下载成功: {args.doi}")
        else:
            print(f"\n✗ 下载失败: {args.doi}")
            print(f"  原因: {result}")
    elif args.batch:
        downloader.batch_download(args.batch, delay_between=args.delay)


if __name__ == "__main__":
    main()

