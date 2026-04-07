import urllib.request
import urllib.parse
import json
import os
import time
from datetime import datetime
from openai import OpenAI

# 1. 配置 API
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
ai_client = None
if API_KEY:
    ai_client = OpenAI(api_key=API_KEY.strip(), base_url="https://api.deepseek.com")

S2_API_KEY = os.environ.get("S2_API_KEY")
if S2_API_KEY:
    S2_API_KEY = S2_API_KEY.strip()

# 2. AI 总结函数
def generate_ai_summary(title, abstract, mode):
    if not ai_client:
        return "AI 总结不可用。"
    
    # 根据不同模式给予不同的 Prompt
    if mode == "classic":
        role_prompt = "1. 价值评估：如果这篇论文是该领域的开创性工作或高被引经典，请在开头加上“🔥 领域经典：”。\n2. 核心观点：用1-2句话精炼总结核心创新点或历史贡献。"
    else:
        role_prompt = "1. 前沿评估：这篇是一篇最新发布的论文，请在开头加上“🆕 最新速递：”。\n2. 核心观点：用1-2句话精炼总结它的研究方向或最新突破。"

    prompt = f"""
    你是一个脉冲神经网络(SNN)领域的顶级专家。请阅读以下论文：
    {role_prompt}
    不要翻译原摘要。
    论文标题: {title}
    论文摘要: {abstract}
    """
    try:
        response = ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个严谨的学术阅读助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, 
            max_tokens=150
        )
        time.sleep(1.5) # 防止大模型并发限制
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI 总结失败: {e}")
        return "AI 总结生成失败。"

# 3. 核心抓取逻辑 (增加 mode 参数)
def fetch_papers(mode="classic"):
    query = 'spiking neural network CSNN'
    fields = 'title,abstract,url,year,venue,citationCount,publicationDate'
    
    # 如果是找最新论文，限制在近两年
    if mode == "latest":
        current_year = datetime.now().year
        url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}&limit=100&year={current_year-1}-{current_year}&fields={fields}'
    else:
        url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}&limit=100&fields={fields}'
    
    headers = {}
    if S2_API_KEY:
        headers['x-api-key'] = S2_API_KEY

    try:
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req, timeout=30)
        data = json.loads(response.read().decode('utf-8'))
        
        raw_papers = [item for item in data.get('data', []) if item.get('abstract')]
            
        # 根据模式进行排序
        if mode == "classic":
            raw_papers = sorted(raw_papers, key=lambda x: x.get('citationCount', 0), reverse=True)
            print("--- 开始处理【经典名人堂】 ---")
        else:
            raw_papers = sorted(raw_papers, key=lambda x: x.get('publicationDate') or '1970-01-01', reverse=True)
            print("--- 开始处理【每日新前沿】 ---")
        
        # 为了不让请求时间太长，各取前 20 篇
        top_papers = raw_papers[:30]
        papers = []
        
        for i, item in enumerate(top_papers):
            title = item.get('title', 'Unknown Title')
            pub_date = item.get('publicationDate') or str(item.get('year', 'Unknown'))
            link = item.get('url', '#')
            citations = item.get('citationCount', 0)
            venue = item.get('venue') or "Journal/Conference"
            
            print(f"[{i+1}/20] 处理中: {title[:30]}...")
            ai_viewpoint = generate_ai_summary(title, item.get('abstract'), mode)
            
            papers.append({
                'title': f"[{venue}] {title}",
                'published': pub_date,
                'link': link,
                'summary': item.get('abstract')[:150] + '...', 
                'ai_summary': ai_viewpoint,
                'citations': citations         
            })
            
        return papers
    except Exception as e:
        print(f"❌ {mode} 抓取发生错误: {e}")
        return []

if __name__ == '__main__':
    # 分别抓取两波数据
    classic_papers = fetch_papers(mode="classic")
    latest_papers = fetch_papers(mode="latest")
    
    if classic_papers or latest_papers:
        # 把两份数据存进同一个 JSON 文件中
        with open('papers.json', 'w', encoding='utf-8') as f:
            json.dump({
                "updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                "classic_papers": classic_papers,
                "latest_papers": latest_papers
            }, f, ensure_ascii=False, indent=2)
        print("✅ 双频道数据更新完毕！")
