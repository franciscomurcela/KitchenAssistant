from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo import monitoring
from datetime import datetime
import requests
import logging
import json
import time
import os

# Configuração do MongoDB
uri = "mongodb+srv://PECI:evaluation@peci.ss2x5.mongodb.net/?retryWrites=true&w=majority&appName=PECI"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.assistente_cozinha  # Nome da base de dados
logs_collection = db.logs  # Coleção para armazenar logs
counters_collection = db.counters  # Coleção para armazenar contadores
feedback_collection = client.assessment_db.feedback_logs  # Agora grava no sítio certo
feedback_state_collection = client.assessment_db.feedback_state  # Coleção para armazenar o estado do feedback

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataManager")

PRIORITY_FILE = 'informations/priority.json'
INTENT_FILE = 'informations/intents.json'

# Função para enviar sinal ao assessment manager
def send_signal_to_assessment_manager(intent):

    print("Aguardo 5 segundos antes de enviar o sinal...")
    time.sleep(5)

    url = "http://localhost:5002/evaluate"
    data = {"intent": intent}
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            logger.info(f"Sinal enviado ao assessment manager para o intent: {intent}")
        else:
            logger.error(f"Falha ao enviar sinal ao assessment manager: {response.status_code}")
    except Exception as e:
        logger.error(f"Erro ao enviar sinal ao assessment manager: {e}")


# Função para processar novos logs
def process_new_log(log):
    # if log is None or not isinstance(log, dict):
    #     logger.warning("Log inválido ou None recebido.")
    #     return
    # if log.get("from_feedback") == True:
    #     return
    # nlu = log.get("nlu")
    # if not isinstance(nlu, dict):
    #     logger.warning("Campo 'nlu' inválido ou ausente no log.")
    #     return
    print("Log recebido:", log)
    intent = log.get("intent")
    if intent:
        counter = counters_collection.find_one({"intent": intent})
        if counter:
            if counter == 0:
                send_signal_to_assessment_manager(intent)
            new_count = counter["count"] + 1
            counters_collection.update_one({"intent": intent}, {"$set": {"count": new_count}})
        else:
            new_count = 1
            send_signal_to_assessment_manager(intent)
            counters_collection.insert_one({"intent": intent, "count": new_count})

        logger.info(f"Intent {intent} count atualizado para {new_count}")

        limit = get_limit_by_intent(intent)
        if limit is not None:
            if new_count >= limit:
                send_signal_to_assessment_manager(intent)
                counters_collection.update_one({"intent": intent}, {"$set": {"count": 0}})  # Resetar o contador
        else:
            print(f"Limite para {intent}: {limit}")
            

def get_limit_by_intent(received_intent):
    try:
        with open(INTENT_FILE, 'r') as f_intents:
            intent_groups = json.load(f_intents).get("intent_groups", {})

        with open(PRIORITY_FILE, 'r') as f_priorities:
            priority_groups = json.load(f_priorities).get("priority_groups", {})

        priority = intent_groups.get(received_intent)
        if priority:
            limit = priority_groups.get(priority)
            return limit
        else:
            return None  # Intent not found

    except FileNotFoundError:
        print("Error: One or both JSON files were not found.")
        return None
    except json.JSONDecodeError:
        print("Error: Problem reading the JSON files.")
        return None

# Só processa feedback se 'from_feedback' for True
def process_feedback(log):

    if log.get("from_feedback") == True:
        logger.info("Log de feedback detetado. Estado será desativado.")

        #desativa o estado de feedback no MongoDB
        feedback_state_collection.update_one(
            {"_id": "feedback_state"},
            {"$set": {"state": "inactive"}}
        )

        #avisa assessment manager para enviar feedback stop para a máquina de estados
        try:
            response = requests.post(
                "http://localhost:5002/feedback/state",
                json={"state": "inactive"}
            )
            if response.status_code == 200:
                logger.info("Estado de feedback desativado com sucesso via AssessmentManager.")
            else:
                logger.warning(f"Falha ao notificar AssessmentManager: {response.status_code}")
        except Exception as e:
            logger.error(f"Erro ao notificar AssessmentManager: {e}")

# Função para ouvir mudanças na coleção de logs
def listen_to_logs():
    with logs_collection.watch() as stream:
        for change in stream:
            if change["operationType"] == "insert":
                log = change["fullDocument"]
                process_new_log(log)

                #Depois, se estiver em modo feedback, guarda o feedback
                feedback_state = feedback_state_collection.find_one({"_id": "feedback_state"})
                if feedback_state and feedback_state["state"] and log.get("from_feedback") == True:
                    if log.get("from_feedback") == True:
                        logger.info("Log de feedback recebido. Estado de feedback será encerrado.")
                        process_feedback(log)

                        # Desativa o estado após processar um feedback
                        feedback_state_collection.update_one(
                            {"_id": "feedback_state"},
                            {"$set": {"state": "inactive"}}
                        )

if __name__ == "__main__":
    logger.info("Iniciando DataManager...")
    listen_to_logs()
