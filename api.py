from flask import Flask, request, jsonify
import requests
import json
import logging
import os
from bs4 import BeautifulSoup

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
ACCESS_KEYS = set(os.getenv("ACCESS_KEYS", "").split(","))

class UnlimitedAIClient:
    def __init__(self, base_url="https://unlimitedai.org"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.ajax_url = f"{self.base_url}/wp-admin/admin-ajax.php"
        self.common_headers = {
            "accept": "*/*",
            "accept-language": "pt-BR,pt;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "origin": self.base_url,
            "referer": f"{self.base_url}/",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Microsoft Edge";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "priority": "u=1, i"
        }
        self.post_id = "18"
        self.chatbot_identity = "shortcode"
        self.wpaicg_chat_client_id = "a5UlxWnSOp"
        self.default_chat_id = "2149"
        self.chat_history = []
        self.wpnonce = self.fetch_nonce()

    def fetch_nonce(self):
        response = self.session.get(f"{self.base_url}/", headers=self.common_headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        nonce_input = soup.find("input", {"name": "_wpnonce"})
        if nonce_input:
            return nonce_input["value"]
        raise ValueError("Não foi possível encontrar o _wpnonce.")

    def send_message(self, message):
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
            return self._extract_response_text(response.text)
        except Exception as e:
            logging.error("Erro ao enviar mensagem: %s", e)
            return "Erro ao processar a resposta."

    def _extract_response_text(self, response_text):
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

client = UnlimitedAIClient()

@app.route("/")
def home():
    return "API está rodando com sucesso! 🚀"

@app.route("/api/chat", methods=["POST"])
def chat():
    auth_key = request.headers.get("Authorization")
    if not auth_key or auth_key not in ACCESS_KEYS:
        return jsonify({"error": "Acesso não autorizado."}), 403
    
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Mensagem não fornecida."}), 400
    
    response = client.send_message(data["message"])
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
