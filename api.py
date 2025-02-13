import requests
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class UnlimitedAIClient:
    def __init__(self):
        self.base_url = "https://unlimitedai.org"
        self.session = requests.Session()
        
        self.ajax_url = f"{self.base_url}/wp-admin/admin-ajax.php"
        
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
        
        # Parâmetros fixos (confirme se ainda são válidos)
        self.wpnonce = "80cf09c997"
        self.post_id = "18"
        self.chatbot_identity = "shortcode"
        self.wpaicg_chat_client_id = "a5UlxWnSOp"
        self.default_chat_id = "27847"
        
        # Histórico do chat para manter o contexto
        self.chat_history = []

    def send_message(self, message):
        """ Envia uma mensagem ao chatbot e retorna a resposta formatada """
        
        # Adiciona a nova entrada ao histórico do chat
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
        """ Filtra os dados JSON e reconstrói a resposta da IA """
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

if __name__ == "__main__":
    client = UnlimitedAIClient()
    
    print("\n🤖 Bem-vindo ao chat! Digite sua mensagem para conversar com a IA.")
    print("Digite 'sair' para encerrar o chat.\n")

    while True:
        user_input = input("Você: ")
        
        if user_input.lower() == "sair":
            print("Encerrando o chat...")
            break
        
        response = client.send_message(user_input)
        print(f"\n🟢 IA: {response}\n")

