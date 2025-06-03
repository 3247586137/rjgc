1# coding=utf-8
import json
import requests
import re
from personality_parameters import PersonalityAnalyzer
import database

class InteractiveChatClient:
    def __init__(self, api_key: str, endpoint: str, model_name: str):
        self.api_key = api_key
        self.endpoint = endpoint
        self.model_name = model_name
        self.analyzer = PersonalityAnalyzer()
        self._init_headers()
        self.active_user = None

    def _init_headers(self):
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

    def _build_prompt(self, user_input: str) -> dict:
        personality = self.analyzer.generate_profile(self.active_user)
        history = database.get_latest_message(3, self.active_user)
        
        system_msg = {
            "role": "system",
            "content": f"""
            根据当前性格参数生成回复：
            {json.dumps(personality, ensure_ascii=False)}
            对话历史：{self._format_history(history)}
            """
        }

        return {
            "model": self.model_name,
            "messages": [system_msg, {"role": "user", "content": user_input}],
            "temperature": 0.6 + personality['傲娇指数']*0.3 - (1-personality['温柔度'])*0.2,
            "stream": False
        }

    def _format_history(self, history: list) -> str:
        return "\n".join(f"用户：{msg[0]}\n{msg[1]}" for msg in history) if history else ""

    def _clean_response(self, text: str) -> str:
        return re.sub(r'[\(（].*?[\)）]', '', text).strip()

    def start_session(self,id,input):
        self.active_user = id
        print("对话开始")
        try:
            user_input = input
            response = self._get_response(user_input)
            if response:
                return response
                
        except KeyboardInterrupt:
            print("\n对话中断")

    def _get_response(self, user_input: str) -> str:
        try:
            payload = self._build_prompt(user_input)
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=5000
            )
            
            if response.status_code == 200:
                result = response.json()
                clean_text = self._clean_response(result['choices'][0]['message']['content'])
                cleaned_text = clean_text.replace("回复：", "", 1)
                database.write_into_database(self.active_user, user_input, cleaned_text)
                return clean_text
            return "请求失败，状态码：{response.status_code}"
            
        except Exception:
            return "生成错误：{str(e)}"

def play(input):
    service = InteractiveChatClient(
        api_key="HZW_hJZTCHSHKp2WKkqaMh5YnTbnbGuWX-K7RmSbjXKnX-CiJ4sjie_0J9nvocpUKr8tPSV7ejmVeOPtYJgGBw",
        endpoint="https://maas-cn-southwest-2.modelarts-maas.com/v1/infers/8a062fd4-7367-4ab4-a936-5eeb8fb821c4/v1/chat/completions",
        model_name="DeepSeek-R1"
    )
    return service.start_session(1,input)


if __name__ == '__main__':
    input="有什么计划吗"
    aichat=play(input)
    print(aichat)