import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import os
import time
from datetime import datetime
from openai import OpenAI

API_KEY = os.environ.get("DEEPSEEK_API_KEY")
client = None
if API_KEY:
    client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")
else:
    print("警告：未检测到 DEEPSEEK_API_KEY 环境变量，AI 总结功能将跳过。")

def generate_ai_summary(title, abstract):
    if not client:
        return "AI 总结不可用（未配置 API 密钥）。"
    
    # 巧妙的提示词：让 AI 充当评审，判断价值并总结
    prompt = f"""
    你是一个类脑计算、CSNN 和人工智能领域的顶级评审专家。请阅读以下论文：
    1. 价值评估：如果这篇论文提出了重大理论突破、极具潜力的神经形态硬件架构，或解决了关键难题，请在回复的最开头加上“🔥 重点推荐：”。如果是常规研究，则不需要加。
    2. 核心观点：用 1-2 句话（中文）极其精炼地总结它的**核心创新点**。不要翻译原摘要。
    
    论文标题: {title}
    论文摘要: {abstract}
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个严谨的学术阅读助手，擅长评估论文价值并提取核心信息。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, 
            max_tokens=150
        )
        time.sleep(1) 
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI 总结失败: {e}")
        return "AI 总结生成失败。"

def fetch_papers():
    search_query = 'abs:"spiking neural network" OR abs:"CSNN" OR abs:"neuromorphic" OR abs:"brain-inspired"'
    url = f'http://export.arxiv.org/api/query?search_query={urllib.parse.quote(search_query)}&sortBy=submittedDate&sortOrder=desc&max_results=10'
    
    try:
        response = urllib.request.urlopen(url, timeout=15)
        root = ET.fromstring(response.read())
        
        papers = []
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            title = entry.find('{http://www.w3.org/2005/Atom}title').text.replace('\n', ' ')
            published = entry.find('{http://www.w3.org/2005/Atom}published').text[:10]
            link = entry.find('{http://www.w3.org/2005/Atom}id').text
            abstract = entry.find('{http://www.w3.org/2005/Atom}summary').text.replace('\n', ' ').strip()
            
            print(f"正在处理: {title[:30]}...")
            
            ai_viewpoint = generate_ai_summary(title, abstract)
            
            papers.append({
                'title': title,
                'published': published,
                'link': link,
                'summary': abstract[:150] + '...', 
                'ai_summary': ai_viewpoint         
            })
        return papers
    except Exception as e:
        print(f"抓取发生错误: {e}")
        return []

if __name__ == '__main__':
    papers = fetch_papers()
    with open('papers.json', 'w', encoding='utf-8') as f:
        json.dump({
            "updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
            "papers": papers
        }, f, ensure_ascii=False, indent=2)
