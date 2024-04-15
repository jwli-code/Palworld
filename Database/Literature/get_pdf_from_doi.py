# -*- coding: utf-8 -*- 
# @Author: jwli.
# @Date  : 2022/11/11
# version: Python 3.9.2

import requests
from bs4 import BeautifulSoup
import os

import argparse
import sys

parser=argparse.ArgumentParser()
parser._optionals.title = "Flag Arguments"
#parser.add_argument('-pmids',help="Comma separated list of pmids to fetch. Must include -pmids or -pmf.", default='%#$')
parser.add_argument('-doi',help="the file contain doi id each line, the last line should be break", default='%#$')
#parser.add_argument('-out',help="Output directory for fetched articles.  Default: fetched_pdfs", default="fetched_pdfs")
#parser.add_argument('-errors',help="Output file path for pmids which failed to fetch.  Default: unfetched_pmids.tsv", default="unfetched_pmids.tsv")
#parser.add_argument('-maxRetries',help="Change max number of retries per article on an error 104.  Default: 3", default=3,type=int)
args = vars(parser.parse_args())

if len(sys.argv)==1:
    parser.print_help(sys.stderr)
    exit(1)
if args['doi']=='%#$':
    print ("Error: should provide doi file.  Exiting.")
    exit(1)

outf=args['doi'].split('.')[0]
if not os.path.exists(outf):
    print( "Output directory of {0} did not exist.  Created the directory.".format(outf))
    os.mkdir(outf)

errorf=outf + '_error.txt'

path = './' + outf + '/'
#if os.path.exists(path) == False:
#    os.mkdir(path)  #20210607更新，创建保存下载文章的文件夹
f = open(args['doi'], "r", encoding="utf-8")  #存放DOI码的.txt文件中，每行存放一个文献的DOI码，完毕须换行（最后一个也须换行！）
head = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'}  #20210607更新，防止HTTP403错误

for line in f.readlines():
    line = line[:-1] #去换行符
    #url = "https://www.sci-hub.pl/" + line + "#"  #sci hub的DOI码检索url  这个地址已经失效了
    url = "https://www.sci-hub.ren/" + line + "#" #20210515更新：现在换成这个sci hub检索地址
    try:
        download_url = ""  #20211111更新
        r = requests.get(url, headers = head)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, "html.parser")
        #download_url = "https:" + str(soup.div.ul.find(href="#")).split("href='")[-1].split(".pdf")[0] + ".pdf" #寻找出存放该文献的pdf资源地址（该检索已失效）
        if soup.iframe == None:  #20211111更新
            download_url = "https:" + soup.embed.attrs["src"] #20211111更新
        else:
            download_url = soup.iframe.attrs["src"]  #20210515更新
        print(line + " is downloading...\n  --The download url is: " + download_url)
        download_r = requests.get(download_url, headers = head)
        download_r.raise_for_status()
        with open(path + line.replace("/","_") + ".pdf", "wb+") as temp:
            temp.write(download_r.content)
    except:
        with open(errorf, "a+") as error:
            error.write(line + " occurs error!\n")
            if "https://" in download_url:
                error.write(" --The download url is: " + download_url + "\n\n")
    else:
        download_url = ""  #20210801更新
        print(line + " download successfully.\n")
f.close()


