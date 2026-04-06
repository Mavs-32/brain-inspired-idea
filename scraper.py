import json
import os
import time
from datetime import datetime
import arxiv  
from openai import OpenAI

API_KEY = os.environ.get("DEEPSEEK_API_KEY")
ai_client = None
if API_KEY:
    ai_client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")
else:
    print("警告：未检测到 DEEPSEEK_API_KEY 环境变量，AI 总结功能将跳过。")

def generate_ai_summary(title, abstract):
    if not ai_client:
        return "AI 总结不可用（未配置 API 密钥）。"
    
    prompt = f"""
    你是一个脉冲神经网络(SNN)领域的顶级评审专家。请阅读以下论文：
    1. 价值评估：如果这篇论文是该领域的开创性工作或提出了核心基础理论，请在回复的最开头加上“🔥 领域经典：”。
    2. 核心观点：用 1-2 句话（中文）极其精炼地总结它的**核心创新点**。不要翻译原摘要。
    
    论文标题: {title}
    论文摘要: {abstract}
    """
    try:
        response = ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个严谨的学术阅读助手，擅长评估论文价值并提取核心信息。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, 
            max_tokens=150
        )
        time.sleep(1.5) 
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI 总结失败: {e}")
        return "AI 总结生成失败。"

def fetch_papers():
    papers = []
    try:
        # 💡 核心改动 1：关键词极度纯净，只瞄准 SNN 和 CSNN
        # 💡 核心改动 2：限制放宽到 30 篇
        search = arxiv.Search(
            query='all:"spiking neural network" ',
            max_results=30,
            sort_by=arxiv.SortCriterion.Relevance, 
            sort_order=arxiv.SortOrder.Descending
        )
        
        client = arxiv.Client()
        results = list(client.results(search))
        
        for paper in results:
            title = paper.title.replace('\n', ' ')
            published = paper.published.strftime('%Y-%m-%d')
            link = paper.entry_id
            abstract = paper.summary.replace('\n', ' ').strip()
            
            print(f"正在处理: {title[:30]}... (发表于 {published})")
            ai_viewpoint = generate_ai_summary(title, abstract)
            
            papers.append({
                'title': title,
                'published': published,
                'link': link,
                'summary': abstract[:150] + '...', 
                'ai_summary': ai_viewpoint         
            })
            
        print(f"🎉 成功抓取并总结了 {len(papers)} 篇 SNN 高相关性论文！")
        return papers
    except Exception as e:
        print(f"❌ 抓取发生错误: {e}")
        return []

if __name__ == '__main__':
    papers = fetch_papers()
    with open('papers.json', 'w', encoding='utf-8') as f:
        json.dump({
            "updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
            "papers": papers
        }, f, ensure_ascii=False, indent=2)
