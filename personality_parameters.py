import jieba
from typing import Dict, List, Tuple
from database import get_latest_message  # 替换为实际数据库模块名

class PersonalityAnalyzer:
    """
    性格参数生成核心类
    功能：通过分析历史对话生成角色性格维度参数
    """
    def __init__(self):
        # 初始化性格维度词典（可扩展）
        self.personality_dimensions = {
            '傲娇指数': {
                'keywords': ['笨蛋', '才不是', '讨厌', '不要你管', '哼', '才没有'],
                'weight': 1.2  # 权重系数
            },
            '温柔度': {
                'keywords': ['谢谢', '请', '好吗', '辛苦了', '帮帮我', '没关系'],
                'weight': 1.0
            },
            '战斗倾向': {
                'keywords': ['攻击', '斩杀', '必胜', '战技', '敌人', '防御'],
                'weight': 0.8
            }
        }
        
        # 初始化分词组件
        self._init_jieba()

    def _init_jieba(self):
        """加载自定义词典增强分词精度"""
        jieba.add_word('不要你管', freq=2000, tag='v')
        jieba.add_word('才不是', freq=2000, tag='v')
        jieba.add_word('战技', freq=2000, tag='n')

    def _analyze_text(self, text: str) -> Dict[str, float]:
        """
        单文本分析核心方法
        :param text: 待分析文本
        :return: 各维度得分字典
        """
        scores = {dim: 0.0 for dim in self.personality_dimensions}
        words = jieba.lcut(text)
        
        for dim, config in self.personality_dimensions.items():
            hit_count = sum(1 for word in words if word in config['keywords'])
            scores[dim] = hit_count * config['weight']
            
        return scores

    def generate_profile(self, userid: int, n: int = 50) -> Dict[str, float]:
        """
        生成性格参数主接口
        :param userid: 用户ID
        :param n: 分析的对话条数
        :return: 标准化后的性格参数（0.0~1.0）
        """
        # 获取历史对话
        messages = get_latest_message(n, userid)
        if not messages:
            return self._default_profile()

        # 累计得分分析
        total_scores = {dim: 0.0 for dim in self.personality_dimensions}
        total_length = 0
        
        for user_msg, ai_msg in messages:
            # 优先分析AI回复内容
            analysis_result = self._analyze_text(ai_msg)
            
            # 叠加用户对话影响（权重减半）
            user_influence = self._analyze_text(user_msg)
            for dim in analysis_result:
                analysis_result[dim] += user_influence[dim] * 0.5
                
            # 累计总得分和文本长度
            for dim, score in analysis_result.items():
                total_scores[dim] += score
            total_length += len(ai_msg)

        # 标准化处理
        return self._normalize_scores(total_scores, total_length)

    def _normalize_scores(self, scores: Dict[str, float], text_length: int) -> Dict[str, float]:
        """得分标准化处理"""
        if text_length == 0:
            return self._default_profile()

        normalized = {}
        for dim, score in scores.items():
            # 基于文本长度的指数衰减函数
            base_score = score / text_length
            normalized[dim] = round(
                1 / (1 + pow(2, -10 * base_score + 3)),  # Sigmoid标准化
                2
            )
        return normalized

    def _default_profile(self) -> Dict[str, float]:
        """默认性格参数"""
        return {dim: 0.5 for dim in self.personality_dimensions}

# 使用示例
if __name__ == "__main__":
    analyzer = PersonalityAnalyzer()
    # 示例用户分析
    user_id = 1
    profile = analyzer.generate_profile(user_id, n=30)
    
    print("生成性格参数：")
    for dimension, value in profile.items():
        print(f"{dimension}: {value:.2f}")