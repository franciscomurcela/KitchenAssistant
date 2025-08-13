from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

client = MongoClient("mongodb+srv://PECI:evaluation@peci.ss2x5.mongodb.net/?retryWrites=true&w=majority&appName=PECI")

# Escolher a base de dados e coleção
db = client["assistente_cozinha"]
collection = db["logs"]
system_logs_collection = db["logs_sistema"]

app = Flask(__name__)
CORS(app) # Adiciona suporte a CORS

# Configurar o logger
logger = logging.getLogger('proxy_logger')
logger.setLevel(logging.INFO)

# File handler para gravar logs no arquivo
#file_handler = logging.FileHandler('mmi_interactions.log', mode='a')  # 'a' para append
#file_handler.setFormatter(logging.Formatter('%(message)s'))
#logger.addHandler(file_handler)


@app.route('/log', methods=['POST'])
def log():
    data = request.json
    print(data)
    # Verificar se o log é de início ou fim de interação
    if data.get('log') in ["Interação iniciada pelo botão.", "Fim da interação."]:
        system_log_entry = {
            'timestamp': datetime.now().isoformat(),
            'log': data.get('log')
        }
        system_logs_collection.insert_one(system_log_entry)

    return jsonify({'status': 'success'}), 200


@app.errorhandler(404)
def page_not_found(e):
    logger.error(f"404 error: {request.url}")
    return "Not Found", 404

if __name__ == '__main__':
    logger.info("Starting Flask server...")
    app.run(port=5001, debug=True)  # Alterar a porta para 5001