import os
import requests
import json
import logging
from flask import Flask, request, jsonify

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__)

class UnlimitedAIClient:
    def __init__(self):
        self.base_url = "https://unlimitedai.org"
        self.session = requests.Session()
        self.ajax_url = f"{self.base_url}/wp-admin/admin-ajax.php"
        
        # Headers usados na requisição (incluindo cookie)
        self.common_headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "pt-BR,pt;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "no-cache",
            "content-type": "application/x-www-form-urlencoded",
            "origin": self.base_url,
            "pragma": "no-cache",
            "referer": f"{self.base_url}/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
            "cookie": "_ga=GA1.1.234546506.1739333457; fpestid=5XEVNHxuiBBj1BMXZfmz1dGcWf9YyzNHzVm_7VUu83DUaX-aTmFl73EiU01fsPAACqm__Q; cookieyes-consent=consentid:YWtWbnRlY0FKY0JsOXpCY3hhYUZucG9XT3pJOEYzZ2Q,consent:no,action:yes,necessary:yes,functional:no,analytics:no,performance:no,advertisement:no; __gads=ID=4de5dce3a06ef8b3:T=1739333458:RT=1739461344:S=ALNI_MaXG1tmVIazAeRmo_b1UsKCTAC38w; __gpi=UID=00000feee369b45d:T=1739333458:RT=1739461344:S=ALNI_MZhjk2cZkurjbFR6bDtBn1tqAgKpg; __eoi=ID=59a3246d2965adab:T=1739333458:RT=1739461344:S=AA-AfjYHatzBXWSAcvGgX9L0TjFn; FCNEC=%5B%5B%22AKsRol-bl7JDoun8ndcT1KVJqUFh_gre_4b-qkstk3boM5WcD4L5yCFYhipOoE9T3i7B8dD6eEKXkkVL0uzahCYk559iObu5xxGu8Be3W0pFELHbqYPmySubwg2AVSPYnvD8l5dYxzGed2MZO8OfQ2BZ9PCrxMjpkQ%3D%3D%22%5D%5D; cf_clearance=VWqQ.VrVdB9rEO0mIPddwTP5jlfjYkwIOrn2XlQC3tg-1739463201-1.2.1.1-4ibWCXf7rjnam9NSKI4sLGfLqv7BT_QVyZmn0eFMPNl8FchrTUgdBybSLNH6.V9U0eDFxhSh7xMEawP5VgZMaJ.ETivOZtQPnN9HUdYV3IQR3xP55ofHx5QW8l8LjICH.m0Qxp_ecRfOyTR.RUKkl9EgRPJNvcUNAIsDeu2MzdUxTDrBx_SmuX7SeHiQQLZL2f1nk_gCqt44UJsyZ14k6TXS11K5VlOimHaqyeS1wvLTv7n1.gEF1fj4dYKeuGaPb9__0qTOVosP8Rik3Zc70xud6KKlgU1Xl9oH8jWgzF4; _ga_86C1G6297E=GS1.1.1739463184.7.1.1739463201.0.0.0"
        }
        
        # Parâmetros fixos
        self.wpnonce = "80cf09c997"
        self.post_id = "18"
        self.chatbot_identity = "shortcode"
        self.wpaicg_chat_client_id = "a5UlxWnSOp"
        self.default_chat_id = "27847"
        
        # Histórico do chat
        self.chat_history = []

    def send_message(self, message):
        """
        Envia a mensagem para a IA e atualiza o histórico.
        """
        self.chat_history.append({"text": f"Human: {message}"})
        
        payload = {
            "_wpnonce": self.wpnonce,
            "post_id": self.post_id,
            "url": self.base_url,
            "action": "wpaicg_chat_shortcode_message",
            "message": message,
            "bot_id": "0",
            "chatbot_identity": self.chatbot_identity,
            "wpaicg_chat_client_id": self.wpaicg_chat_client_id,
            "wpaicg_chat_history": json.dumps(self.chat_history),
            "chat_id": self.default_chat_id
        }

        try:
            response = self.session.post(self.ajax_url, headers=self.common_headers, data=payload, timeout=10)
            response.raise_for_status()
            ai_response = self._extract_response_text(response.text)
            self.chat_history.append({"text": f"AI: {ai_response}"})
            return ai_response

        except Exception as e:
            logging.error("Erro ao enviar mensagem: %s", e)
            return "Erro ao processar a resposta."

    def _extract_response_text(self, response_text):
        """
        Extrai e monta a resposta da IA a partir do retorno da requisição.
        """
        lines = response_text.split("\n")
        message = ""
        for line in lines:
            if line.startswith("data:"):
                try:
                    data = json.loads(line[6:])
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    if "content" in delta:
                        message += delta["content"]
                except json.JSONDecodeError:
                    continue
        return message.strip() if message else "Resposta não encontrada."

# Instância global do cliente
client = UnlimitedAIClient()

@app.route('/send_message', methods=['POST'])
def send_message_route():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Parâmetro 'message' ausente."}), 400
    
    message = data['message']
    ai_response = client.send_message(message)
    return jsonify({"response": ai_response})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

