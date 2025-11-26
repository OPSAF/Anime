import streamlit as st
import random
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import json
from PIL import Image
import io
import base64

# 设置页面配置
st.set_page_config(
    page_title="🎮 二次元猜谜大冒险",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式 - 增强视觉效果
st.markdown("""
<style>
    .main-title {
        font-size: 3.5rem;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
        text-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .game-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .character-card {
        background: rgba(255,255,255,0.95);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border-left: 5px solid #FF6B6B;
    }
    .hint-box {
        background: linear-gradient(45deg, #FFD166, #FF9E6D);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: white;
        font-weight: bold;
    }
    .score-display {
        font-size: 2rem;
        font-weight: bold;
        background: linear-gradient(45deg, #4ECDC4, #45B7D1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    .combo-display {
        font-size: 1.2rem;
        color: #FF6B6B;
        font-weight: bold;
        animation: pulse 1s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    .mode-button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 0.8rem 1.5rem;
        border-radius: 25px;
        margin: 0.3rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .mode-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

class BangumiGameEngine:
    """游戏引擎类 - 负责游戏逻辑和数据管理"""
    
    def __init__(self):
        # 初始化游戏状态
        self.initialize_game_state()
    
    def initialize_game_state(self):
        """初始化游戏状态"""
        if 'game_engine' not in st.session_state:
            st.session_state.game_engine = {
                'score': 0,
                'combo': 0,
                'max_combo': 0,
                'total_answered': 0,
                'correct_answers': 0,
                'game_mode': 'classic',  # classic, survival, timed, pixel
                'current_character': None,
                'used_characters': set(),
                'hint_level': 0,
                'time_remaining': 60,
                'game_started': False,
                'pixel_level': 10  # 像素化级别
            }
        
        if 'character_data' not in st.session_state:
            st.session_state.character_data = self.get_backup_data()
    
    def crawl_bangumi_characters(self):
        """
        从Bangumi角色排行榜爬取具体角色数据
        直接访问角色页面，避免通用答案
        """
        characters = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            # 直接访问角色排行榜，这里包含具体角色信息
            url = "https://bangumi.tv/character"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 查找角色列表
                character_items = soup.find_all('div', class_='inner')
                
                for item in character_items[:20]:  # 限制数量
                    try:
                        # 提取角色名称
                        name_elem = item.find('h3')
                        if name_elem:
                            name = name_elem.get_text().strip()
                            
                            # 提取作品信息
                            anime_elem = item.find('small', class_='grey')
                            anime = anime_elem.get_text().strip() if anime_elem else "未知作品"
                            
                            # 避免通用答案
                            if "主角" not in name and "主要角色" not in name:
                                # 生成智能提示
                                hint = self.generate_smart_hint(name, anime)
                                
                                characters.append({
                                    'name': name,
                                    'anime': anime,
                                    'hint': hint,
                                    'source': 'bangumi'
                                })
                    except Exception as e:
                        continue
        except Exception as e:
            st.warning(f"爬取数据失败: {str(e)}")
        
        return characters if characters else self.get_backup_data()
    
    def generate_smart_hint(self, name, anime):
        """生成智能提示，避免直接透露答案"""
        hints_db = {
            # 为已知角色提供更具体的提示
            "五条悟": "戴着黑色眼罩的最强咒术师",
            "灶门炭治郎": "使用水之呼吸的温柔少年",
            "阿尼亚·福杰": "会读心术的可爱小女孩",
            "薇尔莉特·伊芙加登": "拥有机械双臂的自动手记人偶",
            "绫波丽": "三无少女的始祖，EVA驾驶员",
            "御坂美琴": "Level 5超能力者，绰号超电磁炮"
        }
        
        if name in hints_db:
            return hints_db[name]
        
        # 通用提示生成逻辑
        anime_keywords = {
            "鬼滅": "使用呼吸法的剑士",
            "咒术": "使用咒力的术师", 
            "SPY": "间谍家庭相关角色",
            "EVA": "EVA驾驶员或相关人物",
            "魔法禁书": "学园都市的能力者"
        }
        
        for keyword, hint in anime_keywords.items():
            if keyword in anime:
                return hint
        
        return f"《{anime}》中的重要角色"
    
    def get_backup_data(self):
        """备用角色数据 - 精心设计的具体角色"""
        return [
            {'name': '五条悟', 'anime': '咒术回战', 'hint': '戴着黑色眼罩的最强咒术师', 'source': 'backup'},
            {'name': '灶门炭治郎', 'anime': '鬼滅之刃', 'hint': '使用水之呼吸的温柔少年', 'source': 'backup'},
            {'name': '阿尼亚·福杰', 'anime': 'SPY×FAMILY', 'hint': '会读心术的可爱小女孩', 'source': 'backup'},
            {'name': '薇尔莉特·伊芙加登', 'anime': '紫罗兰永恒花园', 'hint': '拥有机械双臂的自动手记人偶', 'source': 'backup'},
            {'name': '绫波丽', 'anime': '新世纪福音战士', 'hint': '三无少女的始祖，EVA零号机驾驶员', 'source': 'backup'},
            {'name': '御坂美琴', 'anime': '魔法禁书目录', 'hint': 'Level 5超能力者，绰号超电磁炮', 'source': 'backup'},
            {'name': '立华奏', 'anime': 'Angel Beats!', 'hint': '死后世界的学生会长，被称为天使', 'source': 'backup'},
            {'name': '夏目贵志', 'anime': '夏目友人帐', 'hint': '能够看见妖怪的温柔少年', 'source': 'backup'},
            {'name': 'C.C.', 'anime': '反叛的鲁路修', 'hint': '不老不死的魔女，喜欢披萨', 'source': 'backup'},
            {'name': '鲁迪乌斯·格雷拉特', 'anime': '无职转生', 'hint': '转生到异世界的原家里蹲', 'source': 'backup'},
            {'name': '艾伦·耶格尔', 'anime': '进击的巨人', 'hint': '追求自由的调查兵团成员', 'source': 'backup'},
            {'name': '血小板', 'anime': '工作细胞', 'hint': '在人体内负责止血的可爱细胞', 'source': 'backup'},
            {'name': '炭治郎', 'anime': '鬼滅之刃', 'hint': '戴着日轮耳饰的鬼杀队剑士', 'source': 'backup'},
            {'name': '雷姆', 'anime': 'Re:从零开始的异世界生活', 'hint': '鬼族女仆，对昴忠心耿耿', 'source': 'backup'},
            {'name': '宇智波佐助', 'anime': '火影忍者', 'hint': '宇智波一族的天才忍者', 'source': 'backup'}
        ]
    
    def start_new_game(self, mode='classic'):
        """开始新游戏"""
        st.session_state.game_engine.update({
            'game_mode': mode,
            'game_started': True,
            'current_character': None,
            'hint_level': 0,
            'time_remaining': 60 if mode == 'timed' else 0,
            'pixel_level': 10,
            'used_characters': set()
        })
        self.select_new_character()
    
    def select_new_character(self):
        """选择新角色"""
        available_chars = [c for c in st.session_state.character_data 
                          if c['name'] not in st.session_state.game_engine['used_characters']]
        
        if not available_chars:
            # 如果所有角色都用过了，重置使用记录
            st.session_state.game_engine['used_characters'] = set()
            available_chars = st.session_state.character_data
        
        if available_chars:
            character = random.choice(available_chars)
            st.session_state.game_engine['current_character'] = character
            st.session_state.game_engine['used_characters'].add(character['name'])
            st.session_state.game_engine['hint_level'] = 0
            st.session_state.game_engine['pixel_level'] = 10
    
    def get_current_hint(self):
        """获取当前提示级别对应的提示内容"""
        character = st.session_state.game_engine['current_character']
        if not character:
            return "暂无提示"
        
        hint_level = st.session_state.game_engine['hint_level']
        
        # 分级提示系统
        hints = [
            f"作品提示：{character['anime']}",
            f"角色特征：{character['hint']}",
            f"首字母提示：{character['name'][0]}"
        ]
        
        return hints[min(hint_level, len(hints)-1)]
    
    def use_hint(self):
        """使用提示"""
        if st.session_state.game_engine['hint_level'] < 3:
            st.session_state.game_engine['hint_level'] += 1
    
    def check_answer(self, user_answer):
        """检查答案并更新分数"""
        character = st.session_state.game_engine['current_character']
        if not character:
            return False
        
        correct = user_answer.strip().lower() == character['name'].lower()
        
        if correct:
            # 计算得分
            base_score = 10
            hint_penalty = st.session_state.game_engine['hint_level'] * 2
            combo_bonus = min(st.session_state.game_engine['combo'] // 3, 5)
            
            score_earned = max(base_score - hint_penalty + combo_bonus, 3)
            
            # 更新游戏状态
            st.session_state.game_engine['score'] += score_earned
            st.session_state.game_engine['combo'] += 1
            st.session_state.game_engine['max_combo'] = max(
                st.session_state.game_engine['max_combo'], 
                st.session_state.game_engine['combo']
            )
            st.session_state.game_engine['correct_answers'] += 1
            st.session_state.game_engine['total_answered'] += 1
            
            # 显示成功消息
            st.success(f"🎉 正确！+{score_earned}分 (连击×{st.session_state.game_engine['combo']})")
            
            # 选择新角色
            time.sleep(1)
            self.select_new_character()
            
        else:
            # 错误处理
            st.session_state.game_engine['combo'] = 0
            st.session_state.game_engine['total_answered'] += 1
            st.error(f"❌ 错误！正确答案：{character['name']}")
            time.sleep(2)
            self.select_new_character()
        
        return correct
    
    def get_game_stats(self):
        """获取游戏统计信息"""
        stats = st.session_state.game_engine
        accuracy = (stats['correct_answers'] / stats['total_answered'] * 100) if stats['total_answered'] > 0 else 0
        return {
            'score': stats['score'],
            'combo': stats['combo'],
            'max_combo': stats['max_combo'],
            'accuracy': round(accuracy, 1),
            'total_answered': stats['total_answered']
        }

class GameUI:
    """游戏界面类 - 负责用户界面和交互"""
    
    def __init__(self, game_engine):
        self.game_engine = game_engine
    
    def render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            st.markdown("## 🎯 游戏控制")
            
            # 游戏模式选择
            mode = st.selectbox(
                "选择游戏模式",
                ['classic', 'survival', 'timed', 'pixel'],
                format_func=lambda x: {
                    'classic': '🎮 经典模式',
                    'survival': '💀 生存模式', 
                    'timed': '⏰ 限时挑战',
                    'pixel': '🖼️ 像素猜谜'
                }[x]
            )
            
            if st.button("🚀 开始游戏", use_container_width=True):
                self.game_engine.start_new_game(mode)
            
            st.markdown("---")
            st.markdown("## 📊 游戏统计")
            
            stats = self.game_engine.get_game_stats()
            st.metric("当前分数", stats['score'])
            st.metric("连击次数", stats['combo'])
            st.metric("最高连击", stats['max_combo'])
            st.metric("准确率", f"{stats['accuracy']}%")
            
            st.markdown("---")
            st.markdown("## 🔧 数据管理")
            
            if st.button("🔄 刷新角色数据", use_container_width=True):
                with st.spinner("正在从Bangumi获取数据..."):
                    new_data = self.game_engine.crawl_bangumi_characters()
                    st.session_state.character_data = new_data
                    st.success(f"已加载 {len(new_data)} 个角色")
    
    def render_game_interface(self):
        """渲染游戏主界面"""
        if not st.session_state.game_engine['game_started']:
            self.render_welcome_screen()
        else:
            self.render_playing_screen()
    
    def render_welcome_screen(self):
        """渲染欢迎界面"""
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="main-title">🎮 二次元猜谜大冒险</div>', unsafe_allow_html=True)
            
            st.markdown("""
            <div class="game-container">
                <h2 style="color: white; text-align: center;">欢迎来到创新二次元猜谜游戏！</h2>
                <p style="color: white; text-align: center;">基于Bangumi数据的全新猜谜体验</p>
                
                <div style="text-align: center; margin-top: 2rem;">
                    <h3 style="color: white;">🎯 游戏特色</h3>
                    <p style="color: white;">• 多重提示系统 (Lv.1-3分级提示)</p>
                    <p style="color: white;">• 连击奖励机制 (最高+5分奖励)</p>
                    <p style="color: white;">• 四种游戏模式选择</p>
                    <p style="color: white;">• 实时数据统计</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_playing_screen(self):
        """渲染游戏进行界面"""
        # 显示当前角色信息
        character = st.session_state.game_engine['current_character']
        
        if character:
            # 角色信息卡片
            st.markdown(f"""
            <div class="character-card">
                <h3>🎭 角色猜谜</h3>
                <p><strong>📺 出自作品：</strong>{character['anime']}</p>
                <div class="hint-box">💡 提示：{self.game_engine.get_current_hint()}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 连击显示
            combo = st.session_state.game_engine['combo']
            if combo > 1:
                st.markdown(f'<div class="combo-display">🔥 连击中！当前连击：{combo}</div>', unsafe_allow_html=True)
            
            # 输入区域
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                user_answer = st.text_input("🎯 请输入角色名称：", placeholder="输入你认为的角色名字...", key="answer_input")
            
            with col2:
                st.write("")
                if st.button("✅ 提交答案", use_container_width=True):
                    if user_answer:
                        self.game_engine.check_answer(user_answer)
                    else:
                        st.warning("请输入答案！")
            
            with col3:
                st.write("")
                if st.button("💡 使用提示", use_container_width=True):
                    self.game_engine.use_hint()
                    st.rerun()
            
            # 跳过按钮
            if st.button("⏭️ 跳过此题", use_container_width=True):
                character = st.session_state.game_engine['current_character']
                st.warning(f"跳过了！正确答案是：{character['name']}")
                time.sleep(1)
                self.game_engine.select_new_character()
                st.rerun()

def main():
    """主函数 - 应用入口点"""
    # 初始化游戏引擎
    game_engine = BangumiGameEngine()
    ui = GameUI(game_engine)
    
    # 渲染界面
    ui.render_sidebar()
    ui.render_game_interface()
    
    # 显示角色数据库（可选）
    if st.checkbox("显示角色数据库"):
        characters_df = pd.DataFrame(st.session_state.character_data)
        st.dataframe(characters_df, use_container_width=True)
        
        # 数据统计
        st.subheader("📈 数据统计")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总角色数", len(st.session_state.character_data))
        with col2:
            unique_anime = len(set(char['anime'] for char in st.session_state.character_data))
            st.metric("作品数量", unique_anime)
        with col3:
            source = "Bangumi实时数据" if any(char.get('source') == 'bangumi' for char in st.session_state.character_data) else "示例数据"
            st.metric("数据来源", source)

if __name__ == "__main__":
    main()
