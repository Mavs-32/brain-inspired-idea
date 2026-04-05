import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import os
import time
from datetime import datetime
from openai import OpenAI

# 配置 DeepSeek API
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
client = None
if API_KEY:
    # DeepSeek 完全兼容 OpenAI 的 SDK，只需修改 base_url
    client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")
else:
    print("警告：未检测到 DEEPSEEK_API_KEY 环境变量，AI 总结功能将跳过。")

def generate_ai_summary(title, abstract):
    if not client:
        return "AI 总结不可用（未配置 API 密钥）。"
    
    prompt = f"""
    你是一个类脑计算和人工智能领域的顶级专家。请根据以下论文的标题和摘要，用 1 到 2 句话（必须用中文）极其精炼地总结出这篇论文的**核心创新点或主要观点**。
    不要翻译原摘要，直接说重点。
    
    论文标题: {title}
    论文摘要: {abstract}
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的学术阅读助手，擅长从长篇英文摘要中提取核心价值。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, # 稍微调低温度，让学术总结更严谨
            max_tokens=150
        )
        time.sleep(1) # 稍微停顿，防止触发 API 并发限制
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI 总结失败: {e}")
        return "AI 总结生成失败。"

def fetch_papers():
    # 增加 CSNN 等精准搜索词
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
            
            # 调用 DeepSeek 生成中文摘要
            ai_viewpoint = generate_ai_summary(title, abstract)
            
            papers.append({
                'title': title,
                'published': published,
                'link': link,
                'summary': abstract[:150] + '...', 
                'ai_summary': ai_viewpoint         
            })
        print(f"成功抓取并总结了 {len(papers)} 篇论文！")
        return papers
    except Exception as e:
        print(f"抓取发生错误: {e}")
        return []

if __name__ == '__main__':
    print("开始抓取并调用 DeepSeek 生成总结...")
    papers = fetch_papers()
    with open('papers.json', 'w', encoding='utf-8') as f:
        json.dump({
            "updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
            "papers": papers
        }, f, ensure_ascii=False, indent=2)
    print("全部处理完成！")
