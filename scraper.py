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
    import urllib.request
import urllib.parse
import json
import os
import time
from datetime import datetime
from openai import OpenAI

# DeepSeek 配置
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
ai_client = None
if API_KEY:
    ai_client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

# Semantic Scholar VIP 密钥
S2_API_KEY = os.environ.get("S2_API_KEY")

def generate_ai_summary(title, abstract):
    if not ai_client:
        return "AI 总结不可用。"
    
    prompt = f"""
    你是一个脉冲神经网络(SNN)领域的顶级评审专家。请阅读以下论文：
    1. 价值评估：如果这篇论文是该领域的开创性工作、高被引经典，或提出了核心基础理论，请在开头加上“🔥 领域经典：”。
    2. 核心观点：用 1-2 句话（中文）极其精炼地总结它的**核心创新点**。不要翻译原摘要。
    
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

def fetch_papers():
    # 纯净关键词，只抓 SNN
    query = 'spiking neural network CSNN'
    fields = 'title,abstract,url,year,venue,citationCount'
    
    # 直接拉取 100 篇相关论文进行海选
    url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}&limit=100&fields={fields}'
    
    headers = {}
    if S2_API_KEY:
        headers['x-api-key'] = S2_API_KEY
        print("✅ 成功加载 Semantic Scholar VIP 密钥！")
    else:
        print("⚠️ 未检测到 S2_API_KEY，依然可能被拦截。")

    try:
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req, timeout=30)
        data = json.loads(response.read().decode('utf-8'))
        
        raw_papers = []
        for item in data.get('data', []):
            if not item.get('abstract'):
                continue
            raw_papers.append(item)
            
        # 核心：按引用量从高到低排序
        raw_papers = sorted(raw_papers, key=lambda x: x.get('citationCount', 0), reverse=True)
        
        # 选取引用量最高的 30 篇进行总结
        top_papers = raw_papers[:30]
        papers = []
        
        for i, item in enumerate(top_papers):
            title = item.get('title', 'Unknown Title')
            year = str(item.get('year', 'Unknown'))
            link = item.get('url', '#')
            citations = item.get('citationCount', 0)
            venue = item.get('venue') or "Journal/Conference"
            
            print(f"[{i+1}/30] 正在处理: {title[:30]}... (⭐引用量: {citations})")
            ai_viewpoint = generate_ai_summary(title, item.get('abstract'))
            
            papers.append({
                'title': f"[{venue}] {title}",
                'published': year,
                'link': link,
                'summary': item.get('abstract')[:150] + '...', 
                'ai_summary': ai_viewpoint,
                'citations': citations         
            })
            
        print(f"🎉 成功抓取并总结了 {len(papers)} 篇 SNN 高被引神文！")
        return papers
    except Exception as e:
        print(f"❌ 抓取发生错误: {e}")
        return []

if __name__ == '__main__':
    papers = fetch_papers()
    if papers:
        with open('papers.json', 'w', encoding='utf-8') as f:
            json.dump({
                "updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                "papers": papers
            }, f, ensure_ascii=False, indent=2)
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
