from flask import Flask, request, jsonify
import requests
import json
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Configuração básica
BASE_URL = "https://unlimitedai.org"
AJAX_URL = f"{BASE_URL}/wp-admin/admin-ajax.php"

# Valores fixos (já testados e funcionais)
WPNONCE = "bf53d5e160"  # _wpnonce
POST_ID = "18"
CHATBOT_IDENTITY = "shortcode"
WPAICG_CHAT_CLIENT_ID = "a5UlxWnSOp"
DEFAULT_CHAT_ID = "2149"

# Cabeçalhos HTTP
COMMON_HEADERS = {
    "accept": "*/*",
    "accept-language": "pt-BR,pt;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": f"{BASE_URL}/",
    "origin": BASE_URL,
    "cache-control": "no-cache",
    "pragma": "no-cache"
}

AJAX_HEADERS = COMMON_HEADERS.copy()
AJAX_HEADERS.update({
    "content-type": "application/x-www-form-urlencoded"
})

# Classe para interagir com o chatbot
class UnlimitedAIClient:
    def __init__(self):
        self.session = requests.Session()
        self.chat_history = []

    def send_message(self, message):
        # Adiciona a mensagem ao histórico do chat
        self.chat_history.append({"text": f"Human: {message}"})

        payload = {
            "_wpnonce": WPNONCE,
            "post_id": POST_ID,
            "url": BASE_URL,
            "action": "wpaicg_chat_shortcode_message",
            "message": message,
            "chatbot_identity": CHATBOT_IDENTITY,
            "wpaicg_chat_client_id": WPAICG_CHAT_CLIENT_ID,
            "wpaicg_chat_history": json.dumps(self.chat_history),
            "chat_id": DEFAULT_CHAT_ID
        }

        try:
            response = self.session.post(AJAX_URL, headers=AJAX_HEADERS, data=payload, timeout=10)
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
                    data = json.loads(line[6:])  # Remove "data: " e converte para JSON
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    if "content" in delta:
                        message += delta["content"]  # Monta a resposta
                except json.JSONDecodeError:
                    continue
        return message.strip() if message else "Resposta não encontrada."

# Instância do cliente
client = UnlimitedAIClient()

# Rota inicial
@app.route("/")
def home():
    return "API está rodando com sucesso! 🚀"

# Rota para o chat
@app.route("/api/chat", methods=["POST"])
def chat():
    auth_key = request.headers.get("Authorization")
    if not auth_key or auth_key != "sua_chave_de_acesso_aqui":
        return jsonify({"error": "Acesso não autorizado."}), 403

    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Mensagem não fornecida."}), 400

    response = client.send_message(data["message"])
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


