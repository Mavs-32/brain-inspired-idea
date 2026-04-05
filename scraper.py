import urllib.request
import xml.etree.ElementTree as ET
import json
import os
from datetime import datetime

def fetch_papers():
    # 搜索词已精准包含类脑、SNN 和 CSNN 等相关领域
    search_query = 'all:"brain-inspired" OR all:"spiking neural network" OR all:"CSNN" OR all:"neuromorphic"'
    url = f'http://export.arxiv.org/api/query?search_query={urllib.parse.quote(search_query)}&sortBy=submittedDate&sortOrder=desc&max_results=15'
    
    try:
        response = urllib.request.urlopen(url)
        root = ET.fromstring(response.read())
        
        papers = []
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            papers.append({
                'title': entry.find('{http://www.w3.org/2005/Atom}title').text.replace('\n', ' '),
                'published': entry.find('{http://www.w3.org/2005/Atom}published').text[:10],
                'link': entry.find('{http://www.w3.org/2005/Atom}id').text,
                'summary': entry.find('{http://www.w3.org/2005/Atom}summary').text.replace('\n', ' ').strip()[:250] + '...'
            })
        return papers
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == '__main__':
    papers = fetch_papers()
    # 将数据保存为 json 文件，放到当前目录
    with open('papers.json', 'w', encoding='utf-8') as f:
        json.dump({"updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "papers": papers}, f, ensure_ascii=False, indent=2)
    print("今日论文抓取完毕并已保存到 papers.json")