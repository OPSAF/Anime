import streamlit as st
import random
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import json
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import math

# 设置页面配置
st.set_page_config(
    page_title="🎮 二次元时空侦探",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式 - 增强视觉效果
st.markdown("""
<style>
    .main-title {
        font-size: 4rem;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4, #FFD166);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
        text-shadow: 0 4px 15px rgba(0,0,0,0.3);
        animation: rainbow 3s ease infinite;
    }
    @keyframes rainbow {
        0% { filter: hue-rotate(0deg); }
        100% { filter: hue-rotate(360deg); }
    }
    .game-container {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 25px;
        margin: 1rem 0;
        box-shadow: 0 15px 35px rgba(0,0,0,0.3);
        border: 2px solid rgba(255,255,255,0.1);
    }
    .evidence-card {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 1px solid rgba(255,255,255,0.1);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .evidence-card:hover {
        transform: translateY(-5px);
        background: rgba(255,255,255,0.1);
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .timeline-event {
        background: linear-gradient(45deg, #667eea, #764ba2);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: white;
        font-weight: bold;
        opacity: 0.7;
        transition: all 0.3s ease;
    }
    .timeline-event.active {
        opacity: 1;
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    .character-portrait {
        width: 200px;
        height: 200px;
        border-radius: 20px;
        object-fit: cover;
        border: 3px solid #FFD166;
        box-shadow: 0 10px 25px rgba(255, 209, 102, 0.3);
    }
    .puzzle-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 10px;
        margin: 1rem 0;
    }
    .puzzle-piece {
        width: 100%;
        aspect-ratio: 1;
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .puzzle-piece.revealed {
        background: rgba(255,255,255,0.3);
    }
</style>
""", unsafe_allow_html=True)

class TimeDetectiveGame:
    """时空侦探游戏引擎 - 彻底创新的游戏玩法"""
    
    def __init__(self):
        self.initialize_game_state()
    
    def initialize_game_state(self):
        """初始化游戏状态"""
        if 'game_state' not in st.session_state:
            st.session_state.game_state = {
                'current_mode': 'time_detective',  # 时空侦探模式
                'current_case': None,
                'collected_evidence': [],
                'revealed_clues': 0,
                'time_energy': 100,
                'detective_level': 1,
                'solved_cases': 0,
                'current_timeline': [],
                'timeline_position': 0,
                'character_relationships': {},
                'puzzle_grid': [],
                'game_phase': 'investigation'  # investigation, deduction, conclusion
            }
        
        if 'character_database' not in st.session_state:
            st.session_state.character_database = self.load_character_database()
    
    def load_character_database(self):
        """加载角色数据库 - 优化爬取策略"""
        try:
            # 尝试从Bangumi爬取数据
            characters = self.crawl_bangumi_characters_safe()
            if characters:
                return characters
        except Exception as e:
            st.warning(f"爬取数据失败，使用示例数据: {str(e)}")
        
        # 使用丰富的示例数据
        return self.get_enhanced_backup_data()
    
    def crawl_bangumi_characters_safe(self):
        """安全爬取Bangumi角色数据"""
        characters = []
        try:
            # 使用更稳定的爬取策略
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            # 尝试多个页面
            urls = [
                "https://bangumi.tv/character",
                "https://bangumi.tv/anime/browser?sort=rank"
            ]
            
            for url in urls:
                try:
                    response = requests.get(url, headers=headers, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # 改进的选择器
                        character_elements = (soup.select('.light_odd, .dark_odd, .item') or 
                                            soup.find_all('div', class_=lambda x: x and 'character' in str(x).lower()))
                        
                        for elem in character_elements[:10]:  # 限制数量
                            try:
                                name_elem = (elem.select_one('.name a') or 
                                           elem.select_one('h3 a') or
                                           elem.select_one('a[href*="/character/"]'))
                                
                                if name_elem:
                                    name = name_elem.get_text().strip()
                                    anime_elem = elem.select_one('.info, .grey, small')
                                    anime = anime_elem.get_text().strip() if anime_elem else "未知作品"
                                    
                                    # 创建详细角色档案
                                    character = self.create_character_profile(name, anime)
                                    if character:
                                        characters.append(character)
                                        
                            except Exception:
                                continue
                                
                        if characters:
                            break
                            
                except Exception:
                    continue
                    
        except Exception as e:
            st.error(f"爬取过程中出错: {str(e)}")
        
        return characters if characters else []
    
    def create_character_profile(self, name, anime):
        """创建详细的角色档案"""
        if not name or "主角" in name or "角色" in name:
            return None
            
        # 生成角色特征和背景故事
        traits = self.generate_character_traits(name)
        background = self.generate_background_story(name, anime)
        timeline_events = self.generate_timeline_events(name, anime)
        
        return {
            'name': name,
            'anime': anime,
            'traits': traits,
            'background': background,
            'timeline_events': timeline_events,
            'relationships': self.generate_relationships(name),
            'key_evidence': self.generate_evidence(name, anime),
            'mystery_question': self.generate_mystery_question(name),
            'source': 'bangumi'
        }
    
    def generate_character_traits(self, name):
        """生成角色特征"""
        trait_categories = {
            'appearance': ['发型', '瞳色', '服装', '配饰', '身高', '体型'],
            'personality': ['性格', '习惯', '口头禅', '特长', '弱点', '梦想'],
            'abilities': ['特殊能力', '战斗风格', '职业技能', '隐藏技能']
        }
        
        traits = {}
        for category, trait_list in trait_categories.items():
            traits[category] = {}
            for trait in trait_list:
                # 基于名字生成随机但一致的特征
                random.seed(hash(name + trait))
                traits[category][trait] = self.get_trait_value(trait)
                
        return traits
    
    def get_trait_value(self, trait):
        """获取特征值"""
        trait_values = {
            '发型': ['黑色短发', '金色长发', '蓝色马尾', '红色卷发', '银色波波头', '紫色双马尾'],
            '瞳色': ['碧蓝色', '翠绿色', '琥珀色', '深红色', '紫罗兰色', '金色'],
            '性格': ['开朗活泼', '冷静沉着', '温柔体贴', '傲娇', '天然呆', '腹黑'],
            '特殊能力': ['火焰操控', '时间停止', '读心术', '瞬间移动', '治愈能力', '变身']
        }
        
        return random.choice(trait_values.get(trait, ['未知']))
    
    def generate_background_story(self, name, anime):
        """生成背景故事"""
        stories = [
            f"{name}原本是《{anime}》中的普通学生，直到某天发现了自己的特殊能力",
            f"在《{anime}》的世界里，{name}肩负着重要的使命",
            f"{name}的过去充满了谜团，与《{anime}》的主线剧情密切相关",
            f"作为《{anime}》的关键人物，{name}的命运与整个世界的存亡相连"
        ]
        return random.choice(stories)
    
    def generate_timeline_events(self, name, anime):
        """生成时间线事件"""
        events = []
        base_year = random.randint(2010, 2023)
        
        for i in range(5):
            events.append({
                'year': base_year + i,
                'event': f"{name}在《{anime}》中{'完成了重要任务' if i % 2 == 0 else '经历了重大转折'}",
                'importance': random.randint(1, 5)
            })
            
        return events
    
    def generate_relationships(self, name):
        """生成角色关系"""
        relationships = []
        relation_types = ['盟友', '对手', '朋友', '恋人', '师徒', '家人']
        
        for i in range(3):
            relationships.append({
                'character': f"神秘角色{i+1}",
                'relation': random.choice(relation_types),
                'description': f"与{name}有着复杂的关系"
            })
            
        return relationships
    
    def generate_evidence(self, name, anime):
        """生成关键证据"""
        evidences = [
            f"{name}的日记本，记录着《{anime}》中的重要线索",
            f"一张{name}与神秘人物的合影",
            f"{name}使用的特殊道具",
            f"关于{name}身世的古老文献",
            f"{name}留下的加密信息"
        ]
        return random.choice(evidences)
    
    def generate_mystery_question(self, name):
        """生成谜题问题"""
        questions = [
            f"{name}的真实身份是什么？",
            f"{name}在关键时刻会做出什么选择？",
            f"{name}的特殊能力来自哪里？",
            f"{name}与故事主线有什么关联？"
        ]
        return random.choice(questions)
    
    def get_enhanced_backup_data(self):
        """增强的备用数据"""
        characters = []
        sample_data = [
            ('五条悟', '咒术回战'),
            ('灶门炭治郎', '鬼滅之刃'),
            ('阿尼亚·福杰', 'SPY×FAMILY'),
            ('薇尔莉特·伊芙加登', '紫罗兰永恒花园'),
            ('绫波丽', '新世纪福音战士'),
            ('御坂美琴', '魔法禁书目录'),
            ('立华奏', 'Angel Beats!'),
            ('夏目贵志', '夏目友人帐'),
            ('C.C.', '反叛的鲁路修'),
            ('艾伦·耶格尔', '进击的巨人')
        ]
        
        for name, anime in sample_data:
            character = self.create_character_profile(name, anime)
            if character:
                character['source'] = 'backup'
                characters.append(character)
                
        return characters
    
    def start_new_case(self):
        """开始新的侦探案件"""
        if not st.session_state.character_database:
            st.error("没有可用的角色数据")
            return
            
        # 随机选择一个角色作为案件核心
        case_character = random.choice(st.session_state.character_database)
        
        st.session_state.game_state.update({
            'current_case': case_character,
            'collected_evidence': [],
            'revealed_clues': 0,
            'time_energy': 100,
            'current_timeline': case_character['timeline_events'],
            'timeline_position': 0,
            'game_phase': 'investigation',
            'puzzle_grid': self.generate_puzzle_grid(case_character)
        })
        
        st.success(f"🔍 新案件开始！调查目标：{case_character['name']}")
    
    def generate_puzzle_grid(self, character):
        """生成谜题网格"""
        grid_size = 5
        grid = []
        traits = []
        
        # 收集角色特征作为谜题碎片
        for category, trait_dict in character['traits'].items():
            for trait, value in trait_dict.items():
                traits.append(f"{trait}: {value}")
        
        # 填充网格
        for i in range(grid_size * grid_size):
            if i < len(traits) and i < grid_size * grid_size:
                grid.append({
                    'content': traits[i],
                    'revealed': False,
                    'position': i
                })
            else:
                grid.append({
                    'content': '???',
                    'revealed': False,
                    'position': i
                })
        
        random.shuffle(grid)
        return grid
    
    def collect_evidence(self, evidence_type):
        """收集证据"""
        if st.session_state.game_state['time_energy'] < 10:
            st.warning("⏳ 时间能量不足！")
            return
            
        character = st.session_state.game_state['current_case']
        evidence = None
        
        if evidence_type == 'trait':
            evidence = f"特征线索：{random.choice(list(character['traits']['appearance'].values()))}"
        elif evidence_type == 'background':
            evidence = f"背景线索：{character['background']}"
        elif evidence_type == 'relationship':
            rel = random.choice(character['relationships'])
            evidence = f"关系线索：{rel['character']} - {rel['relation']}"
        
        if evidence and evidence not in st.session_state.game_state['collected_evidence']:
            st.session_state.game_state['collected_evidence'].append(evidence)
            st.session_state.game_state['time_energy'] -= 10
            st.session_state.game_state['revealed_clues'] += 1
            st.success(f"🔎 获得新证据：{evidence}")
    
    def advance_timeline(self):
        """推进时间线"""
        timeline = st.session_state.game_state['current_timeline']
        position = st.session_state.game_state['timeline_position']
        
        if position < len(timeline) - 1:
            st.session_state.game_state['timeline_position'] += 1
            event = timeline[position + 1]
            st.info(f"📅 时间推进到 {event['year']}年：{event['event']}")
    
    def reveal_puzzle_piece(self, position):
        """揭示谜题碎片"""
        grid = st.session_state.game_state['puzzle_grid']
        if not grid[position]['revealed']:
            grid[position]['revealed'] = True
            st.session_state.game_state['time_energy'] -= 5
            st.session_state.game_state['revealed_clues'] += 1
    
    def make_deduction(self, user_answer):
        """做出推理"""
        character = st.session_state.game_state['current_case']
        correct_answer = character['name']
        
        if user_answer.strip().lower() == correct_answer.lower():
            # 计算得分
            clues_used = st.session_state.game_state['revealed_clues']
            energy_remaining = st.session_state.game_state['time_energy']
            base_score = 100
            deduction_score = base_score - clues_used * 5 + energy_remaining // 10
            
            st.session_state.game_state['solved_cases'] += 1
            st.session_state.game_state['detective_level'] = math.ceil(st.session_state.game_state['solved_cases'] / 3)
            
            st.balloons()
            st.success(f"🎯 推理正确！得分：{deduction_score} | 侦探等级提升到 {st.session_state.game_state['detective_level']}")
            
            # 进入下一个案件
            time.sleep(2)
            self.start_new_case()
        else:
            st.session_state.game_state['time_energy'] -= 20
            st.error(f"❌ 推理错误！扣除时间能量")
    
    def get_game_stats(self):
        """获取游戏统计"""
        state = st.session_state.game_state
        return {
            'detective_level': state['detective_level'],
            'solved_cases': state['solved_cases'],
            'time_energy': state['time_energy'],
            'current_clues': state['revealed_clues']
        }

class GameInterface:
    """游戏界面管理器"""
    
    def __init__(self, game_engine):
        self.game = game_engine
    
    def render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            st.markdown("## 🕵️ 侦探档案")
            
            stats = self.game.get_game_stats()
            st.metric("🔍 侦探等级", stats['detective_level'])
            st.metric("✅ 已解决案件", stats['solved_cases'])
            st.metric("⏳ 时间能量", stats['time_energy'])
            st.metric("🔎 收集线索", stats['current_clues'])
            
            st.markdown("---")
            st.markdown("## 🎮 游戏控制")
            
            if st.button("🚀 开始新案件", use_container_width=True):
                self.game.start_new_case()
            
            if st.button("🔄 重新加载数据", use_container_width=True):
                st.session_state.character_database = self.game.load_character_database()
                st.rerun()
    
    def render_investigation_phase(self):
        """渲染调查阶段界面"""
        if not st.session_state.game_state['current_case']:
            st.warning("请先开始一个新案件")
            return
            
        case = st.session_state.game_state['current_case']
        
        # 案件标题
        st.markdown(f'<div class="main-title">🕵️ 时空侦探案件 #{st.session_state.game_state["solved_cases"] + 1}</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 证据收集区域
            st.markdown("### 🔍 证据收集")
            st.markdown("点击按钮收集不同类型的证据：")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📸 收集特征证据", use_container_width=True):
                    self.game.collect_evidence('trait')
            with col2:
                if st.button("📖 收集背景证据", use_container_width=True):
                    self.game.collect_evidence('background')
            with col3:
                if st.button("👥 收集关系证据", use_container_width=True):
                    self.game.collect_evidence('relationship')
            
            # 时间线调查
            st.markdown("### 📅 时间线调查")
            timeline = st.session_state.game_state['current_timeline']
            position = st.session_state.game_state['timeline_position']
            
            for i, event in enumerate(timeline):
                is_active = i == position
                event_class = "timeline-event active" if is_active else "timeline-event"
                st.markdown(f'<div class="{event_class}">{event["year"]}年 - {event["event"]}</div>', unsafe_allow_html=True)
            
            if st.button("⏩ 推进时间线", disabled=position >= len(timeline)-1):
                self.game.advance_timeline()
        
        with col2:
            # 谜题拼图
            st.markdown("### 🧩 特征拼图")
            st.markdown("点击拼图碎片揭示角色特征：")
            
            # 渲染5x5拼图网格
            grid = st.session_state.game_state['puzzle_grid']
            cols = st.columns(5)
            
            for i in range(25):
                with cols[i % 5]:
                    piece = grid[i]
                    if piece['revealed']:
                        st.markdown(f'<div class="puzzle-piece revealed">{piece["content"]}</div>', unsafe_allow_html=True)
                    else:
                        if st.button("?", key=f"puzzle_{i}", use_container_width=True):
                            self.game.reveal_puzzle_piece(i)
                            st.rerun()
    
    def render_deduction_phase(self):
        """渲染推理阶段界面"""
        st.markdown("### 🧠 最终推理")
        st.markdown("基于收集的证据，做出你的最终推理：")
        
        case = st.session_state.game_state['current_case']
        collected_evidence = st.session_state.game_state['collected_evidence']
        
        # 显示收集到的证据
        st.markdown("#### 📋 已收集证据：")
        for evidence in collected_evidence:
            st.markdown(f'<div class="evidence-card">{evidence}</div>', unsafe_allow_html=True)
        
        # 推理输入
        col1, col2 = st.columns([3, 1])
        with col1:
            user_answer = st.text_input("🤔 你认为这个角色是谁？", placeholder="输入角色名称...")
        with col2:
            st.write("")
            st.write("")
            if st.button("🔍 提交推理", use_container_width=True):
                if user_answer:
                    self.game.make_deduction(user_answer)
                    st.rerun()
                else:
                    st.warning("请输入你的推理")
    
    def render_main_interface(self):
        """渲染主界面"""
        if st.session_state.game_state['current_case']:
            # 显示当前案件信息
            case = st.session_state.game_state['current_case']
            
            # 根据游戏阶段渲染不同界面
            if st.session_state.game_state['game_phase'] == 'investigation':
                self.render_investigation_phase()
                
                # 调查完成，进入推理阶段
                if st.session_state.game_state['revealed_clues'] >= 5:
                    st.session_state.game_state['game_phase'] = 'deduction'
                    st.rerun()
                    
            elif st.session_state.game_state['game_phase'] == 'deduction':
                self.render_deduction_phase()
                
        else:
            # 欢迎界面
            self.render_welcome_screen()
    
    def render_welcome_screen(self):
        """渲染欢迎界面"""
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="main-title">🕵️ 二次元时空侦探</div>', unsafe_allow_html=True)
            
            st.markdown("""
            <div class="game-container">
                <h2 style="color: white; text-align: center;">欢迎来到创新的二次元侦探游戏！</h2>
                <p style="color: white; text-align: center;">在这里，你将扮演一名时空侦探，通过收集证据、调查时间线、解开谜题来识别二次元角色</p>
                
                <div style="text-align: center; margin-top: 2rem;">
                    <h3 style="color: #FFD166;">🎯 游戏特色</h3>
                    <p style="color: white;">• 🔍 多维度证据收集系统</p>
                    <p style="color: white;">• 📅 时间线调查机制</p>
                    <p style="color: white;">• 🧩 互动式谜题拼图</p>
                    <p style="color: white;">• 🕵️ 侦探等级成长系统</p>
                    <p style="color: white;">• ⏳ 时间能量管理策略</p>
                </div>
                
                <div style="text-align: center; margin-top: 2rem;">
                    <h3 style="color: #4ECDC4;">🎮 游戏玩法</h3>
                    <p style="color: white;">1. 收集不同类型的证据线索</p>
                    <p style="color: white;">2. 调查角色的时间线事件</p>
                    <p style="color: white;">3. 解开特征拼图谜题</p>
                    <p style="color: white;">4. 基于证据做出最终推理</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚀 开始第一个案件", use_container_width=True, type="primary"):
                self.game.start_new_case()
                st.rerun()

def main():
    """主函数"""
    # 初始化游戏引擎
    game_engine = TimeDetectiveGame()
    game_ui = GameInterface(game_engine)
    
    # 渲染界面
    game_ui.render_sidebar()
    game_ui.render_main_interface()
    
    # 显示角色数据库（调试用）
    if st.checkbox("显示角色数据库（调试）"):
        if st.session_state.character_database:
            # 创建简化的数据框显示
            simplified_data = []
            for char in st.session_state.character_database:
                simplified_data.append({
                    '角色名': char['name'],
                    '作品': char['anime'],
                    '数据源': char['source']
                })
            
            df = pd.DataFrame(simplified_data)
            st.dataframe(df, use_container_width=True)
            
            st.subheader("📊 数据统计")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总角色数", len(st.session_state.character_database))
            with col2:
                unique_anime = len(set(char['anime'] for char in st.session_state.character_database))
                st.metric("作品数量", unique_anime)
            with col3:
                bangumi_count = sum(1 for char in st.session_state.character_database if char.get('source') == 'bangumi')
