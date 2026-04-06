import urllib.request
import urllib.parse
import urllib.error
import json
import os
import time
from datetime import datetime
from openai import OpenAI

# DeepSeek API 配置
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
client = None
if API_KEY:
    client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")
else:
    print("警告：未检测到 DEEPSEEK_API_KEY 环境变量，AI 总结功能将跳过。")

S2_API_KEY = os.environ.get("S2_API_KEY")

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
    # 1. 解除 IEEE 封印，放眼全球顶级期刊和会议
    query = 'spiking neural network neuromorphic CSNN'
    fields = 'title,abstract,url,year,venue,citationCount'
    
    # 2. 扩大搜索范围，抓取前 50 篇高相关性文章
    url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}&limit=50&fields={fields}'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    if S2_API_KEY:
        headers['x-api-key'] = S2_API_KEY

    max_retries = 3
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(req, timeout=20)
            data = json.loads(response.read().decode('utf-8'))
            
            raw_papers = []
            for item in data.get('data', []):
                # 过滤掉没有摘要的无效数据
                if not item.get('abstract'):
                    continue
                raw_papers.append(item)
                
            # 3. 本地掐尖：按引用量从高到低排序，寻找真正的“开山之作”
            raw_papers = sorted(raw_papers, key=lambda x: x.get('citationCount', 0), reverse=True)
            
            # 4. 只取引用量最高的 Top 10 论文发给 AI 总结
            top_papers = raw_papers[:10]
            
            papers = []
            for item in top_papers:
                title = item.get('title', 'Unknown Title')
                year = str(item.get('year', 'Unknown'))
                link = item.get('url', '#')
                citations = item.get('citationCount', 0)
                
                # 获取发表来源，如果没有则显示 General
                venue = item.get('venue')
                if not venue:
                    venue = "Journal/Conference"
                
                print(f"💎 正在处理神文: [{venue}] {title[:20]}... (年份: {year}, ⭐ 引用量: {citations})")
                
                ai_viewpoint = generate_ai_summary(title, item.get('abstract'))
                
                papers.append({
                    'title': f"[{venue}] {title}",
                    'published': year,
                    'link': link,
                    'summary': item.get('abstract')[:150] + '...', 
                    'ai_summary': ai_viewpoint,
                    'citations': citations         
                })
                
            print(f"🎉 成功抓取并总结了 {len(papers)} 篇高价值经典论文！")
            return papers
            
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"⚠️ 触发频率限制 (429)，准备重试... (第 {attempt + 1}/{max_retries} 次尝试)")
                time.sleep(15) 
            else:
                print(f"❌ 抓取发生错误: {e}")
                return []
        except Exception as e:
            print(f"❌ 发生未知错误: {e}")
            return []
            
    print("❌ 重试次数耗尽，Semantic Scholar 拒绝了访问。")
    return []

if __name__ == '__main__':
    papers = fetch_papers()
    if papers: 
        with open('papers.json', 'w', encoding='utf-8') as f:
            json.dump({
                "updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                "papers": papers
            }, f, ensure_ascii=False, indent=2)
