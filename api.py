from flask import Flask, request, jsonify
import requests
import json
import logging
import time

app = Flask(__name__)

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Chaves de acesso válidas (pode ser substituído por um banco de dados)
ACCESS_KEYS = {"chave_secreta_123"}

class UnlimitedAIClient:
    def __init__(self, base_url="https://unlimitedai.org"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.ajax_url = f"{self.base_url}/wp-admin/admin-ajax.php"
        self.common_headers = {
            "accept": "*/*",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        self.ajax_headers = self.common_headers.copy()
        self.ajax_headers.update({
            "content-type": "application/x-www-form-urlencoded",
            "origin": self.base_url,
            "referer": f"{self.base_url}/",
        })
        self.wpnonce = "bf53d5e160"
        self.post_id = "18"
        self.chatbot_identity = "shortcode"
        self.wpaicg_chat_client_id = "a5UlxWnSOp"
        self.default_chat_id = "2149"
        self.chat_history = []
    
    def send_message(self, message):
        self.chat_history.append({"text": f"Human: {message}"})
        payload = {
            "_wpnonce": self.wpnonce,
            "post_id": self.post_id,
            "url": self.base_url,
            "action": "wpaicg_chat_shortcode_message",
            "message": message,
            "chatbot_identity": self.chatbot_identity,
            "wpaicg_chat_client_id": self.wpaicg_chat_client_id,
            "wpaicg_chat_history": json.dumps(self.chat_history),
            "chat_id": self.default_chat_id
        }
        try:
            response = self.session.post(self.ajax_url, headers=self.ajax_headers, data=payload, timeout=10)
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
    app.run(host="0.0.0.0", port=5000)
