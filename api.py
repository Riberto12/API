from flask import Flask, request, jsonify
import requests
import json
import logging
import os

app = Flask(__name__)

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Chaves de acesso válidas (pode ser substituído por um banco de dados)
ACCESS_KEYS = set(os.getenv("ACCESS_KEYS", "").split(","))

class UnlimitedAIClient:
    def __init__(self, base_url="https://unlimitedai.org"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.ajax_url = f"{self.base_url}/wp-admin/admin-ajax.php"
        
        # Cabeçalhos que imitam o comportamento de um navegador real
        self.common_headers = {
            "accept": "*/*",
            "accept-language": "pt-BR,pt;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0"
        }
        self.ajax_headers = self.common_headers.copy()
        self.ajax_headers.update({
            "content-type": "application/x-www-form-urlencoded",
            "origin": self.base_url,
            "referer": f"{self.base_url}/",
        })
        
        # Parâmetros fixos (verifique se estes valores permanecem válidos)
        self.wpnonce = "bf53d5e160"
        self.post_id = "18"
        self.chatbot_identity = "shortcode"
        self.wpaicg_chat_client_id = "a5UlxWnSOp"
        self.default_chat_id = "2149"
        
        # Histórico do chat para manter o contexto
        self.chat_history = []
    
    def send_message(self, message):
        """ Envia uma mensagem ao chatbot e retorna a resposta formatada """
        # Adiciona a nova entrada ao histórico do chat
        self.chat_history.append({"text": f"Human: {message}"})
        
        # Payload completo, conforme a versão que funciona interativamente
        payload = {
            "_wpnonce": self.wpnonce,
            "post_id": self.post_id,
            "url": self.base_url,
            "action": "wpaicg_chat_shortcode_message",
            "message": message,
            "bot_id": "0",  # Parâmetro essencial presente na versão interativa
            "chatbot_identity": self.chatbot_identity,
            "wpaicg_chat_client_id": self.wpaicg_chat_client_id,
            "wpaicg_chat_history": json.dumps(self.chat_history),
            "chat_id": self.default_chat_id
        }

        # Log de payload antes de enviar
        logging.info(f"Enviando payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = self.session.post(self.ajax_url, headers=self.ajax_headers, data=payload, timeout=10)
            
            # Verificando o status da resposta
            logging.info(f"Status code da resposta: {response.status_code}")
            response.raise_for_status()

            # Log da resposta do servidor
            logging.info(f"Resposta do servidor: {response.text}")
            
            return self._extract_response_text(response.text)
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro na requisição: {e}")
            return f"Erro ao processar a resposta: {e}"
    
    def _extract_response_text(self, response_text):
        """ Filtra os dados JSON e reconstrói a resposta da IA """
        lines = response_text.split("\n")
        message = ""
        for line in lines:
            if line.startswith("data:"):
                try:
                    data = json.loads(line[6:])  # Remove "data:" e converte para JSON
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
    
    response_message = client.send_message(data["message"])
    return jsonify({"response": response_message})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)




