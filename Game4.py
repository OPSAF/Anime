import streamlit as st
import random
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import json

# 设置页面
st.set_page_config(
    page_title="二次元猜谜游戏",
    page_icon="🎮",
    layout="wide"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #ff6b6b;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .game-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    .character-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .score-display {
        font-size: 1.5rem;
        font-weight: bold;
        color: #4ecdc4;
    }
    .loading-spinner {
        text-align: center;
        padding: 2rem;
    }
    .debug-info {
        background: #f0f0f0;
        padding: 10px;
        border-radius: 5px;
        font-family: monospace;
        font-size: 12px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def crawl_bangumi_data_safe():
    """安全地从Bangumi.tv爬取数据，适应Streamlit Cloud环境"""
    characters_data = []
    
    try:
        # 更安全的请求头设置
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        # 使用更稳定的URL和选择器
        test_urls = [
            "https://bangumi.tv/anime/browser?sort=hot",
            "https://bangumi.tv/anime/browser?sort=rank"
        ]
        
        for i, url in enumerate(test_urls):
            try:
                st.write(f"尝试爬取URL: {url}")
                response = requests.get(url, headers=headers, timeout=20, verify=False)
                
                if response.status_code != 200:
                    st.warning(f"请求失败，状态码: {response.status_code}")
                    continue
                    
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 调试：显示页面标题
                page_title = soup.find('title')
                if page_title:
                    st.write(f"页面标题: {page_title.get_text()}")
                
                # 尝试多种选择器
                anime_selectors = [
                    '.subjectItem', 
                    '.item', 
                    '.browserItem',
                    '.subject'
                ]
                
                anime_items = None
                for selector in anime_selectors:
                    anime_items = soup.select(selector)
                    if anime_items:
                        st.write(f"使用选择器 '{selector}' 找到 {len(anime_items)} 个动画")
                        break
                
                if not anime_items:
                    st.warning("未找到动画列表，尝试备用选择器...")
                    # 备用选择器
                    anime_items = soup.find_all('div', class_=lambda x: x and 'subject' in x) or \
                                 soup.find_all('li', class_=lambda x: x and 'item' in x)
                
                st.write(f"总共找到 {len(anime_items)} 个动画项目")
                
                for j, item in enumerate(anime_items[:10]):  # 限制数量
                    try:
                        # 多种方式获取标题
                        title_elem = (item.select_one('h3 a') or 
                                    item.select_one('.title a') or 
                                    item.select_one('a[href*="/subject/"]'))
                        
                        if not title_elem:
                            continue
                            
                        anime_title = title_elem.get_text().strip()
                        href = title_elem.get('href', '')
                        anime_url = "https://bangumi.tv" + href if href.startswith('/') else href
                        
                        if not anime_url.startswith('http'):
                            continue
                            
                        st.write(f"处理动画: {anime_title}")
                        
                        # 添加延迟
                        time.sleep(2)
                        
                        # 尝试获取角色信息（简化版）
                        char_data = get_character_info_safe(anime_url, anime_title, headers)
                        characters_data.extend(char_data)
                        
                    except Exception as e:
                        st.write(f"处理动画时出错: {str(e)}")
                        continue
                        
                break  # 如果第一个URL成功，就不尝试第二个
                
            except requests.exceptions.RequestException as e:
                st.write(f"网络请求错误: {str(e)}")
                continue
            except Exception as e:
                st.write(f"解析错误: {str(e)}")
                continue
                
    except Exception as e:
        st.error(f"数据爬取总体失败: {str(e)}")
    
    # 如果爬取到数据，保存到session state供调试
    if characters_data:
        st.session_state.last_crawled_data = characters_data
        st.success(f"成功爬取到 {len(characters_data)} 个角色数据！")
    else:
        st.warning("未能爬取到数据，将使用示例数据")
        characters_data = get_backup_data()
    
    return characters_data

def get_character_info_safe(anime_url, anime_title, headers):
    """安全地获取角色信息"""
    characters = []
    
    try:
        response = requests.get(anime_url, headers=headers, timeout=10, verify=False)
        if response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 尝试多种角色选择器
        char_selectors = [
            '#browserItemList .light_odd',
            '#browserItemList .dark_odd',
            '.characters .item',
            '.person'
        ]
        
        char_elements = None
        for selector in char_selectors:
            char_elements = soup.select(selector)
            if char_elements:
                break
        
        if not char_elements:
            char_elements = soup.find_all('div', class_=lambda x: x and 'character' in str(x).lower())
        
        for char_elem in char_elements[:3]:  # 每个动画只取前3个角色
            try:
                name_elem = (char_elem.select_one('.name a') or 
                           char_elem.select_one('a[href*="/character/"]') or
                           char_elem.select_one('a[href*="/person/"]'))
                
                if name_elem:
                    char_name = name_elem.get_text().strip()
                    
                    # 获取角色描述
                    desc_elem = (char_elem.select_one('.info') or 
                               char_elem.select_one('.bio') or
                               char_elem.select_one('.summary'))
                    
                    hint = desc_elem.get_text().strip() if desc_elem else f"来自《{anime_title}》的角色"
                    hint = re.sub(r'\s+', ' ', hint)
                    if len(hint) > 50:
                        hint = hint[:50] + "..."
                    
                    characters.append({
                        "name": char_name,
                        "anime": anime_title,
                        "hint": hint,
                        "url": anime_url
                    })
                    
            except Exception as e:
                continue
                
    except Exception as e:
        st.write(f"获取角色信息错误: {str(e)}")
    
    # 如果没找到角色，创建示例角色
    if not characters:
        characters.append({
            "name": f"{anime_title}主角",
            "anime": anime_title,
            "hint": f"《{anime_title}》的主要角色",
            "url": anime_url
        })
    
    return characters

def get_backup_data():
    """备用数据"""
    return [
        {"name": "灶门炭治郎", "anime": "鬼滅の刃", "hint": "使用水之呼吸的温柔少年", "url": ""},
        {"name": "阿尼亚·福杰", "anime": "SPY×FAMILY", "hint": "会读心术的可爱小女孩", "url": ""},
        {"name": "五条悟", "anime": "咒术回战", "hint": "最强的咒术师，戴着黑色眼罩", "url": ""},
        {"name": "薇尔莉特·伊芙加登", "anime": "紫罗兰永恒花园", "hint": "拥有机械双臂的自动手记人偶", "url": ""},
        {"name": "鲁迪乌斯·格雷拉特", "anime": "无职转生", "hint": "转生到异世界的原家里蹲", "url": ""},
        {"name": "绫波丽", "anime": "新世纪福音战士", "hint": "三无少女的始祖，EVA零号机驾驶员", "url": ""},
        {"name": "立华奏", "anime": "Angel Beats!", "hint": "死后世界的学生会长，被称为天使", "url": ""},
        {"name": "御坂美琴", "anime": "魔法禁书目录", "hint": "Level 5超能力者，绰号超电磁炮", "url": ""},
        {"name": "夏目贵志", "anime": "夏目友人帐", "hint": "能够看见妖怪的温柔少年", "url": ""},
        {"name": "C.C.", "anime": "反叛的鲁路修", "hint": "不老不死的魔女，喜欢披萨", "url": ""}
    ]

# 初始化游戏状态
def init_game_state():
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'current_character' not in st.session_state:
        st.session_state.current_character = None
    if 'attempts' not in st.session_state:
        st.session_state.attempts = 0
    if 'game_started' not in st.session_state:
        st.session_state.game_started = False
    if 'hint_used' not in st.session_state:
        st.session_state.hint_used = False
    if 'characters' not in st.session_state:
        st.session_state.characters = get_backup_data()
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'use_crawled_data' not in st.session_state:
        st.session_state.use_crawled_data = False
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False

# 开始新游戏
def start_new_game():
    st.session_state.game_started = True
    st.session_state.attempts = 0
    st.session_state.hint_used = False
    if st.session_state.characters:
        available_chars = [c for c in st.session_state.characters if c != st.session_state.current_character]
        st.session_state.current_character = random.choice(available_chars if available_chars else st.session_state.characters)

# 检查答案
def check_answer(user_answer):
    correct_answer = st.session_state.current_character['name']
    if user_answer.strip().lower() == correct_answer.lower():
        points = 7 if st.session_state.hint_used else 10
        st.session_state.score += points
        st.success(f"🎉 正确答案！+{points}分")
        time.sleep(1)
        start_new_game()
        return True
    else:
        st.session_state.attempts += 1
        if st.session_state.attempts >= 3:
            st.error(f"❌ 游戏结束！正确答案是：{correct_answer}")
            time.sleep(2)
            start_new_game()
        else:
            st.warning(f"⚠️ 答案错误！还剩{3 - st.session_state.attempts}次机会")
        return False

# 加载Bangumi数据
def load_bangumi_data():
    with st.spinner('正在从Bangumi.tv获取最新数据...'):
        try:
            # 禁用SSL验证以适应Streamlit Cloud
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            crawled_data = crawl_bangumi_data_safe()
            if crawled_data and len(crawled_data) > 0:
                st.session_state.characters = crawled_data
                st.session_state.data_loaded = True
                st.session_state.use_crawled_data = True
            else:
                st.session_state.characters = get_backup_data()
                st.session_state.data_loaded = True
                st.session_state.use_crawled_data = False
        except Exception as e:
            st.error(f"数据加载失败: {str(e)}")
            st.session_state.characters = get_backup_data()
            st.session_state.data_loaded = True
            st.session_state.use_crawled_data = False

# 主应用
def main():
    # 初始化游戏状态
    init_game_state()
    
    # 标题
    st.markdown('<div class="main-header">🎮 二次元猜谜游戏 · 猜猜呗</div>', unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.header("游戏信息")
        st.markdown(f'<div class="score-display">当前分数: {st.session_state.score}</div>', unsafe_allow_html=True)
        
        st.write("游戏规则：")
        st.write("1. 根据提示猜出角色名称")
        st.write("2. 每次游戏有3次机会")
        st.write("3. 使用提示会扣除3分")
        st.write("4. 答对一题得10分（使用提示得7分）")
        
        st.header("数据管理")
        if st.button("🔄 从Bangumi获取最新数据"):
            load_bangumi_data()
        
        if st.button("🔄 使用示例数据"):
            st.session_state.characters = get_backup_data()
            st.session_state.data_loaded = True
            st.session_state.use_crawled_data = False
            st.success("已切换到示例数据！")
        
        st.header("调试选项")
        st.session_state.debug_mode = st.checkbox("启用调试模式")
        
        if st.session_state.debug_mode:
            st.write("数据状态:")
            st.write(f"- 数据加载: {st.session_state.data_loaded}")
            st.write(f"- 使用爬取数据: {st.session_state.use_crawled_data}")
            st.write(f"- 角色数量: {len(st.session_state.characters)}")
            
            if st.button("显示爬取数据"):
                if hasattr(st.session_state, 'last_crawled_data'):
                    st.json(st.session_state.last_crawled_data)
                else:
                    st.write("暂无爬取数据")
    
    # 游戏主界面
    if not st.session_state.game_started:
        st.markdown("""
        <div class="game-container">
            <h2 style="color: white; text-align: center;">欢迎来到二次元猜谜游戏！</h2>
            <p style="color: white; text-align: center;">基于Bangumi番组计划的角色数据库</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 显示数据源信息
        if st.session_state.data_loaded:
            data_source = "Bangumi实时数据" if st.session_state.use_crawled_data else "示例数据"
            st.info(f"当前使用: {data_source} | 角色数量: {len(st.session_state.characters)}")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 开始游戏", use_container_width=True, type="primary"):
                if not st.session_state.data_loaded:
                    load_bangumi_data()
                start_new_game()
    
    else:
        # 显示当前角色信息
        character = st.session_state.current_character
        
        st.markdown(f"""
        <div class="character-card">
            <h3>角色信息</h3>
            <p><strong>出自作品：</strong>{character['anime']}</p>
            <p><strong>提示：</strong>{character['hint']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 用户输入
        col1, col2 = st.columns([3, 1])
        with col1:
            user_answer = st.text_input("请输入角色名称：", placeholder="输入你认为的角色名字...", key="answer_input")
        with col2:
            st.write("")
            st.write("")
            if st.button("提交答案", use_container_width=True, type="primary"):
                if user_answer:
                    check_answer(user_answer)
                else:
                    st.warning("请输入答案！")
        
        # 提示按钮
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("💡 使用提示", use_container_width=True) and not st.session_state.hint_used:
                st.session_state.hint_used = True
                st.info(f"额外提示：这个角色出自《{character['anime']}》")
        
        # 跳过按钮
        if st.button("⏭️ 跳过此题", use_container_width=True):
            st.warning(f"跳过了！正确答案是：{character['name']}")
            time.sleep(1)
            start_new_game()
    
    # 显示角色数据库
    st.header("📚 Bangumi角色数据库")
    if st.checkbox("显示所有可用角色"):
        characters_df = pd.DataFrame(st.session_state.characters)
        st.dataframe(characters_df, use_container_width=True)
        
        # 显示数据统计
        st.subheader("数据统计")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("角色数量", len(st.session_state.characters))
        with col2:
            unique_anime = len(set(char['anime'] for char in st.session_state.characters))
            st.metric("作品数量", unique_anime)
        with col3:
            data_source = "Bangumi.tv" if st.session_state.use_crawled_data else "示例数据"
            st.metric("数据来源", data_source)

if __name__ == "__main__":
    main()
