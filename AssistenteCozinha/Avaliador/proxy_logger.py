from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
import json
from datetime import datetime
import xml.etree.ElementTree as ET

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

# Stream handler para imprimir logs na consola
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(console_handler)

# Função para extrair campos específicos do XML
def extract_fields_from_xml(xml_str):
    root = ET.fromstring(xml_str)
    namespace = {'mmi': 'http://www.w3.org/2008/04/mmi-arch', 'emma': 'http://www.w3.org/2003/04/emma'}
    
    extension_notification_elem = root.find('.//mmi:ExtensionNotification', namespace)
    interpretation_elem = root.find('.//emma:interpretation', namespace)
    command_elem = interpretation_elem.find('.//command') if interpretation_elem is not None else None
    
    source = extension_notification_elem.get('{http://www.w3.org/2008/04/mmi-arch}source') if extension_notification_elem is not None else None
    target = extension_notification_elem.get('{http://www.w3.org/2008/04/mmi-arch}target') if extension_notification_elem is not None else None
    command = command_elem.text if command_elem is not None else None
    
    logger.info(f"Extracted source: {source}")
    logger.info(f"Extracted target: {target}")
    logger.info(f"Extracted command: {command}")

    nlu = None
    
    if command:
        try:
            command_data = json.loads(command)
            nlu = command_data.get('nlu')
            logger.info(f"Extracted nlu: {nlu}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from command: {e}")
    
    return {
        'source': source,
        'target': target,
        'nlu': nlu
    }



# Função para registrar logs
def log_interaction(data):
    timestamp = datetime.now().isoformat()

    # Verificar se o log é XML
    try:
        extracted_data = extract_fields_from_xml(data['log'])
        log_entry = {
            'timestamp': timestamp,
            'source': extracted_data['source'],
            'target': extracted_data['target'],
            'nlu': extracted_data['nlu']
        }
    except ET.ParseError:
        # Se não for XML, registrar como texto simples
        log_entry = {
            'timestamp': timestamp,
            'log': data['log']
        }

    logger.info(json.dumps(log_entry))
    print("ADDING LOG TO MONGODB")
    collection.insert_one(log_entry)




@app.route('/log', methods=['POST'])
def log():
    data = request.json

    # Verificar se o log é de início ou fim de interação
    if data.get('log') in ["Interação iniciada pelo botão.", "Fim da interação."]:
        system_log_entry = {
            'timestamp': datetime.now().isoformat(),
            'log': data.get('log')
        }
        system_logs_collection.insert_one(system_log_entry)
    else:
        # Processar logs complexos (XML)
        log_interaction(data)

    return jsonify({'status': 'success'}), 200




@app.route('/proxy', methods=['POST', 'GET'])
def proxy():
    logger.info(f"Received {request.method} request")
    if request.method == 'POST':
        target_url = request.args.get('target')
        logger.info(f"POST request to {target_url} with data: {request.json}")
        try:
            response = requests.post(target_url, json=request.json)
            logger.info(f"POST request to {target_url} succeeded with status code {response.status_code}")
            log_interaction({
                'method': 'POST',
                'url': target_url,
                'request': request.json,
                'response': response.json()
            })
            return jsonify(response.json())
        except Exception as e:
            logger.error(f"POST request to {target_url} failed: {e}")
            return jsonify({'error': str(e)}), 500
    elif request.method == 'GET':
        target_url = request.args.get('target')
        logger.info(f"GET request to {target_url}")
        try:
            response = requests.get(target_url)
            logger.info(f"GET request to {target_url} succeeded with status code {response.status_code}")
            log_interaction({
                'method': 'GET',
                'url': target_url,
                'response': response.json()
            })
            return jsonify(response.json())
        except Exception as e:
            logger.error(f"GET request to {target_url} failed: {e}")
            return jsonify({'error': str(e)}), 500
        



@app.errorhandler(404)
def page_not_found(e):
    logger.error(f"404 error: {request.url}")
    return "Not Found", 404

if __name__ == '__main__':
    logger.info("Starting Flask server...")
    app.run(port=5001, debug=True)  # Alterar a porta para 5001