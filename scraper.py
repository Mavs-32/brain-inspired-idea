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

# 2. AI 总结函数 (保留并强化)
def generate_ai_summary(title, abstract, mode):
    if not ai_client:
        return "AI 总结不可用。"
    
    # 针对不同频道定制不同的专家身份和分析重点
    if mode == "classic":
        role_prompt = "1. 价值评估：如果是该领域的开创性工作，请在开头加上“🔥 领域经典：”。\n2. 核心观点：用1-2句话精炼总结其历史地位或核心创新。"
    elif mode == "multi_agent":
        role_prompt = "1. 协作评估：这是一个关于多智能体(Multi-Agent)的研究，请在开头加上“🤖 多智协作：”。\n2. 核心观点：重点分析 SNN 如何应用于智能体协作、强化学习或通信优化。"
    else:
        role_prompt = "1. 前沿评估：这篇是最新发布的论文，请在开头加上“🆕 最新速递：”。\n2. 核心观点：总结其在 CSNN 或 SNN 领域的最新突破。"

    prompt = f"""
    你是一个脉冲神经网络(SNN)与群体智能领域的顶级专家。请阅读以下论文：
    {role_prompt}
    注意：直接给出总结，不要翻译原摘要，字数控制在 100 字以内。
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
            max_tokens=200
        )
        time.sleep(1.5) # 频率限制保护
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI 总结失败: {e}")
        return "AI 总结生成失败。"

# 3. 核心抓取逻辑
def fetch_papers(mode="classic"):
    # 动态调整搜索词
    if mode == "multi_agent":
        query = 'spiking neural network "multi-agent" reinforcement learning'
    else:
        query = 'spiking neural network CSNN'
        
    fields = 'title,abstract,url,year,venue,citationCount,publicationDate'
    
    # 筛选时间：经典看历史，最新/多智能体看近三年
    current_year = datetime.now().year
    if mode == "classic":
        url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}&limit=100&fields={fields}'
    else:
        url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}&limit=100&year={current_year-2}-{current_year}&fields={fields}'
    
    headers = {'x-api-key': S2_API_KEY} if S2_API_KEY else {}

    try:
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req, timeout=30)
        data = json.loads(response.read().decode('utf-8'))
        
        raw_papers = [item for item in data.get('data', []) if item.get('abstract')]
            
        # 排序逻辑
        if mode == "classic":
            raw_papers = sorted(raw_papers, key=lambda x: x.get('citationCount', 0), reverse=True)
            print("--- 处理【经典名人堂】 ---")
        elif mode == "multi_agent":
            raw_papers = sorted(raw_papers, key=lambda x: (x.get('citationCount', 0), x.get('year', 0)), reverse=True)
            print("--- 处理【多智能体前沿】 ---")
        else:
            raw_papers = sorted(raw_papers, key=lambda x: x.get('publicationDate') or '1970-01-01', reverse=True)
            print("--- 处理【每日新前沿】 ---")
        
        top_papers = raw_papers[:20] # 每个频道取 20 篇
        papers = []
        
        for i, item in enumerate(top_papers):
            title = item.get('title', 'Unknown Title')
            print(f"[{mode}][{i+1}/20] AI 总结中: {title[:30]}...")
            
            ai_viewpoint = generate_ai_summary(title, item.get('abstract'), mode)
            
            papers.append({
                'title': f"[{item.get('venue') or 'Journal'}] {title}",
                'published': item.get('publicationDate') or str(item.get('year', 'Unknown')),
                'link': item.get('url', '#'),
                'ai_summary': ai_viewpoint,
                'citations': item.get('citationCount', 0)
            })
            
        return papers
    except Exception as e:
        print(f"❌ {mode} 抓取错误: {e}")
        return []

if __name__ == '__main__':
    data_store = {
        "updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "classic_papers": fetch_papers(mode="classic"),
        "latest_papers": fetch_papers(mode="latest"),
        "multi_agent_papers": fetch_papers(mode="multi_agent") # 新频道
    }
    
    with open('papers.json', 'w', encoding='utf-8') as f:
        json.dump(data_store, f, ensure_ascii=False, indent=2)
    print("✅ 全频道数据（含 AI Summary）更新完毕！")
