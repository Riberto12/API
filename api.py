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
        
        # Headers usados na requisição (copiados do script original)
        self.common_headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "pt-BR,pt;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "no-cache",
            "content-type": "application/x-www-form-urlencoded",
            "origin": self.base_url,
            "pragma": "no-cache",
            "referer": f"{self.base_url}/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0"
        }
        
        # Parâmetros fixos
        self.wpnonce = "80cf09c997"
        self.post_id = "18"
        self.chatbot_identity = "shortcode"
        self.wpaicg_chat_client_id = "a5UlxWnSOp"
        self.default_chat_id = "27847"
        
        # Histórico do chat (global para essa instância)
        self.chat_history = []

    def send_message(self, message):
        """
        Envia a mensagem para a IA e atualiza o histórico.
        """
        # Adiciona o input do usuário ao histórico
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
            # Adiciona a resposta da IA ao histórico
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
                    data = json.loads(line[6:])  # Remove "data: " e converte para JSON
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
    """
    Endpoint para receber uma mensagem e retornar a resposta da IA.
    Requisição (JSON):
      {
         "message": "Sua mensagem aqui"
      }
    Resposta (JSON):
      {
         "response": "Resposta da IA"
      }
    """
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Parâmetro 'message' ausente."}), 400
    
    message = data['message']
    ai_response = client.send_message(message)
    return jsonify({"response": ai_response})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

