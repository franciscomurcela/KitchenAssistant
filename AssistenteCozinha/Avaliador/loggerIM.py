from websocket import WebSocketApp
import ssl
import xml.etree.ElementTree as ET
import json
from datetime import datetime
from pymongo import MongoClient
import random
import signal
import sys

# URL do WebSocket
websocket_url = "wss://localhost:8005/IM/USER1/APP"


# Escolher a base de dados e coleção
db = client.assistente_cozinha
collection = db.logs
feedback_collection = db.feedback
users_collection = db.users_assistant

user_sent_to_assessment = False #flag para verificar se o utilizador foi enviado para o assessment

#função para selecionar um utilizador disponível
def select_available_user():
    user_doc = users_collection.find_one_and_update(
        {"estado": "inativo"},
        {"$set": {"estado": "ativo"}},
        return_document=True
    )
    return user_doc if user_doc else None

# Função para adicionar timestamp ao log
def log_with_timestamp():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return timestamp

def source_Target(root):
    # Para encontrar o valor de 'mmi:source', precisamos encontrar o elemento 'mmi:startRequest'
    start_request = root.find('{http://www.w3.org/2008/04/mmi-arch}startRequest')
    # Agora podemos acessar o atributo 'mmi:source' desse elemento
    if start_request is not None:
        source_value = start_request.get('{http://www.w3.org/2008/04/mmi-arch}source')
        # E para encontrar o valor de 'mmi:target' fazemos algo parecido
        target_value = start_request.get('{http://www.w3.org/2008/04/mmi-arch}target')
        return source_value, target_value
    else:
        print(f"{log_with_timestamp()} - Não foi possível encontrar a informação 'mmi:source'.")
        return None, None

def confidence_Mode(root):
        emma_interpretation = root.find('.//{http://www.w3.org/2003/04/emma}interpretation')
        # Se encontrarmos o elemento, podemos pegar o valor do atributo 'emma:confidence'
        if emma_interpretation is not None:
            confidence_value = emma_interpretation.get('{http://www.w3.org/2003/04/emma}confidence')
            mode_value = emma_interpretation.get('{http://www.w3.org/2003/04/emma}mode')
            return confidence_value, mode_value
        else:
            print(f"{log_with_timestamp()} - Não foi possível encontrar a informação 'emma:confidence'.")
            return None, None

def intent_Text(root):
    emma_element = root.find('.//{http://www.w3.org/2003/04/emma}emma')
    if emma_element is not None:
        # Navega para o elemento <emma:interpretation> dentro de <emma:emma>
        interpretation_element = emma_element.find('.//{http://www.w3.org/2003/04/emma}interpretation')

        if interpretation_element is not None:
            # Navega para o elemento <command> dentro de <emma:interpretation>
            command_element = interpretation_element.find('command')

            # Se o elemento <command> for encontrado, imprime o seu texto
            if command_element is not None:
                # Pega o texto dentro de <command>
                command_text = command_element.text

                # Transforma o texto JSON em um dicionário Python
                try:
                    command_data = json.loads(command_text)

                    # Acessa o valor de 'nlu'
                    if 'nlu' in command_data:
                        nlu_value = command_data['nlu']

                        # Agora acessamos os valores dentro de 'nlu' usando os seus nomes (chaves)
                        intent_value = nlu_value.get('intent')
                        audio_reconized_value = nlu_value.get('audioReconized')
                        return intent_value, audio_reconized_value
                    else:
                        print(f"{log_with_timestamp()} - Não encontrei a chave 'nlu' dentro de <command>.")
                        return None, None

                except json.JSONDecodeError:
                    print(f"{log_with_timestamp()} - O texto dentro de <command> não está em formato JSON válido.")
                    return None, None
            else:
                print(f"{log_with_timestamp()} - Elemento <command> não encontrado.")
                return None, None
        else:
            print(f"{log_with_timestamp()} - Não encontrei o elemento <emma:interpretation> dentro de <emma:emma>.")
            return None, None
    else:
        print(f"{log_with_timestamp()} - Não encontrei o elemento <emma:emma>.")
        return None, None

def verify_intent(intent):
    with open("informations/intents.json", "r") as file:
        data = json.load(file)

    intent_groups = data.get("intent_groups", {})
    #print("Intent groups:", intent_groups)
    #print("Intent recebido:", intent)   
    if intent in intent_groups:
        return True
    else:
        return False
    
# Adicionar funcionalidade para carregar utilizadores do ficheiro JSON
'''def load_users():
    with open("informations/users.json", "r") as file:
        users_data = json.load(file)
    return {user["id"]: user["name"] for user in users_data["users"]}

def get_random_user_id():
    users = load_users()
    user_ids = list(users.keys())
    if user_ids:
        return user_ids[random.randint(0, min(2, len(user_ids) - 1))]
    return None'''

def on_message(ws, message):

    global user_sent_to_assessment
    global selected_user

    print(f"{log_with_timestamp()} - Log recebido: {message}")
    #users = load_users()  # Carregar utilizadores do ficheiro JSON

    #user_id = get_random_user_id()  # Obter um ID de utilizador aleatório
    #user_name = users.get(user_id, "Desconhecido")
    
    user_id = selected_user["user"]
    user_name = selected_user["nome"]

    # Enviar info do utilizador ao AssessmentManager (só uma vez)
    if not user_sent_to_assessment:
        try:
            import websocket  # importar aqui para evitar conflitos
            ws_notify = websocket.create_connection("ws://localhost:8765")
            payload = json.dumps({
                "type": "user_info",
                "user_id": user_id,
                "nome": user_name
            })
            ws_notify.send(payload)
            ws_notify.close()
            print(f"{log_with_timestamp()} - Utilizador enviado ao AssessmentManager: {user_id}")
            user_sent_to_assessment = True
        except Exception as e:
            print(f"{log_with_timestamp()} - ⚠️ Erro ao enviar utilizador ao AssessmentManager: {e}")
            

    try:
        root = ET.fromstring(message)
        time = log_with_timestamp()
        source, target = source_Target(root)
        confidence, mode = confidence_Mode(root)
        intent, audio_reconized = intent_Text(root)

        print(f"{time} - Mensagem recebida e processada.")
        print(f"  source: {source}")
        print(f"  target: {target}")
        print(f"  confidence: {confidence}")
        print(f"  mode: {mode}")
        print(f"  intent: {intent}")
        print(f"  audioReconized: {audio_reconized}")
            
        log_entry = {
            'utilizador_id': user_id,  # Adicionar ID do utilizador
            'utilizador_nome': user_name,  # Adicionar nome do utilizador
            'timestamp': time,
            'source': source,
            'target': target,
            'confidence': confidence,
            'mode': mode,
            'intent': intent,
            'audioReconized': audio_reconized
        }
        # Verificar se o sistema está em modo feedback
        feedback_state = client.assessment_db.feedback_state.find_one({"_id": "feedback_state"})
        feedback_active = feedback_state and feedback_state.get("state") == "active"

        print("ADICIONANDO LOG AO MONGODB")
        if feedback_active:
            if source == "FUSION":
                print(f"{log_with_timestamp()} - Ignorado: feedback vindo do FUSION (evitar duplicação)")
                return
            
            log_entry["from_feedback"] = True
            log_entry["original_intent"] = intent  # Guarda o intent real para referência
            log_entry["intent"] = "feedback"       # Substitui pelo intent forçado
            #feedback_collection.insert_one(log_entry)
            print(f"{log_with_timestamp()} - Log de feedback guardado com intent forçado: 'feedback'")

            print("Feedback está ativo — a enviar sinal para terminar.")
            try:
                import requests
                response = requests.post(
                    "http://localhost:5002/feedback/state",
                    json={"state": "inactive"}
                )
                if response.status_code == 200:
                    print("Feedback desativado com sucesso.")
                else:
                    print(f"Falha ao desativar feedback: {response.status_code}")
            except Exception as e:
                print(f"Erro ao comunicar com o AssessmentManager: {e}")

        else:
            print("Feedback não está ativo.")
            print(verify_intent(intent))
            if verify_intent(intent):
                collection.insert_one(log_entry)
                print(f"{log_with_timestamp()} - Log normal guardado com intent: {intent}")
            else:
                print(f"{log_with_timestamp()} - Intent não reconhecido e fora do modo feedback — log ignorado.")

    except ET.ParseError:
        print(f"{log_with_timestamp()} - Erro ao analisar a mensagem XML: {message}")
    except Exception as e:
        print(f"{log_with_timestamp()} - Ocorreu um erro ao processar a mensagem: {e}")

def on_error(ws, error):
    print(f"{log_with_timestamp()} - Erro no WebSocket: {error}")

def on_close(ws, close_status_code, close_msg):
    global selected_user
    print(f"{log_with_timestamp()} - Conexão WebSocket fechada.")
    print(f"  Código de status: {close_status_code}")
    print(f"  Mensagem de fechamento: {close_msg}")
    if selected_user:
        users_collection.update_one(
            {"user": selected_user["user"]},
            {"$set": {"estado": "inativo"}}
        )
        print(f"{log_with_timestamp()} - Utilizador {selected_user['user']} marcado como inativo.")

def on_open(ws):
    print(f"{log_with_timestamp()} - Conexão WebSocket aberta.")

def cleanup_and_exit(signum, frame):
    global selected_user
    if selected_user:
        users_collection.update_one(
            {"user": selected_user["user"]},
            {"$set": {"estado": "inativo"}}
        )
        print(f"{log_with_timestamp()} - Utilizador {selected_user['user']} marcado como inativo (via signal handler).")
    sys.exit(0)

if __name__ == '__main__':
    # Adiciona handlers para SIGINT e SIGTERM
    signal.signal(signal.SIGINT, cleanup_and_exit)
    signal.signal(signal.SIGTERM, cleanup_and_exit)

    selected_user = select_available_user()
    if selected_user:
        print(f"Utilizador selecionado: {selected_user['nome']} ({selected_user['user']})")
    else:
        print("❌ Nenhum utilizador disponível!")
        exit()

    ws = WebSocketApp(websocket_url,
                      on_open=on_open,
                      on_message=on_message,
                      on_error=on_error,
                      on_close=on_close)

    # Para se conectar a um WebSocket seguro (wss), precisamos passar o contexto SSL
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
