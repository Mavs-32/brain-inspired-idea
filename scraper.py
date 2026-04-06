import urllib.request
import urllib.parse
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
    
    prompt = f"""
    你是一个类脑计算和人工智能领域的顶级专家。请阅读以下经典论文：
    1. 价值评估：如果这篇论文是该领域的开创性工作、高被引经典，或提出了核心基础理论，请在开头加上“🔥 领域经典：”。
    2. 核心观点：用 1-2 句话（中文）极其精炼地总结它的**核心创新点或历史贡献**。不要翻译原摘要。
    
    论文标题: {title}
    论文摘要: {abstract}
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个严谨的学术助手，擅长评估论文的历史价值并提取核心信息。"},
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
    # 搜索词加入了 IEEE，限定在计算机科学/工程领域，搜索全年代的高相关性论文
    query = '("spiking neural network" OR "neuromorphic" OR "CSNN") AND "IEEE"'
    
    # fields 参数要求返回：标题,摘要,链接,年份,发表期刊/会议,引用量
    fields = 'title,abstract,url,year,venue,citationCount'
    url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}&limit=15&fields={fields}'
    
    try:
        # Semantic Scholar 也需要简单的 User-Agent 伪装
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        response = urllib.request.urlopen(req, timeout=20)
        data = json.loads(response.read().decode('utf-8'))
        
        papers = []
        for item in data.get('data', []):
            abstract = item.get('abstract')
            # 跳过没有摘要的论文
            if not abstract:
                continue
                
            title = item.get('title', 'Unknown Title')
            year = str(item.get('year', 'Unknown'))
            link = item.get('url', '#')
            citations = item.get('citationCount', 0)
            venue = item.get('venue', 'IEEE/Other')
            
            print(f"正在处理: {title[:30]}... (发表于 {year}, 引用量: {citations})")
            
            ai_viewpoint = generate_ai_summary(title, abstract)
            
            papers.append({
                'title': f"[{venue}] {title}", # 在标题前加上期刊/会议名称
                'published': year,
                'link': link,
                'summary': abstract[:150] + '...', 
                'ai_summary': ai_viewpoint,
                'citations': citations         # 新增：保存引用量数据
            })
            
        # 在本地按“引用量”从高到低排序，确保最牛的论文排在最前面
        papers = sorted(papers, key=lambda x: x.get('citations', 0), reverse=True)
        
        print(f"🎉 成功抓取并总结了 {len(papers)} 篇高价值经典论文！")
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
