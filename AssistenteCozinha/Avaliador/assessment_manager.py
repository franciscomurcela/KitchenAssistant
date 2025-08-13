from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import logging
import asyncio
import websockets
import random
import ssl
import json
import os
# -------------------------------
# Configuração do MongoDB
# -------------------------------
client = MongoClient(uri)
db = client.assessment_db
feedback_collection = db.feedback_logs
feedback_state_collection = db.feedback_state
event_loop = None  # Loop principal será definido no main
current_user = {"user_id": None, "nome": None} #variável global para armazenar o utilizador atual

# -------------------------------
# Flask App
# -------------------------------
app = Flask(__name__)
CORS(app)

# -------------------------------
# WebSocket
# -------------------------------
connected_clients = set()
message_queue = asyncio.Queue()


async def notify_clients():
    while True:
        message = await message_queue.get()  # Espera até ter uma nova mensagem
        if connected_clients:
            print(f"Enviando mensagem para {len(connected_clients)} cliente(s): {message}")
            encoded_message = message.encode("utf-8").hex()  # Codifica a mensagem em base 16
            await asyncio.gather(*(client.send(encoded_message) for client in connected_clients))
            print("Enviado")
        else:
            print("Nenhum cliente WebSocket conectado.")
        message_queue.task_done()

async def websocket_handler(websocket):
    connected_clients.add(websocket)
    print("Novo cliente WebSocket conectado.")
    try:
        async for message in websocket:
            try:
                # Tenta decodificar mensagem (caso venha codificada em hex)
                try:
                    message = bytes.fromhex(message).decode("utf-8")
                except:
                    pass  # mensagem já está em texto normal

                data = json.loads(message)
                if data.get("type") == "user_info":
                    current_user["user_id"] = data.get("user_id")
                    current_user["nome"] = data.get("nome")
                    print(f"[User Info] Utilizador recebido: {current_user}")
            except Exception as e:
                print(f"[WebSocket] Erro ao processar mensagem recebida: {e}")
    except websockets.exceptions.ConnectionClosed:
        print("Cliente WebSocket desconectado.")
    finally:
        connected_clients.remove(websocket)

async def watch_feedback_logs():
    print("A escutar a coleção feedback_logs por novos feedbacks...")

    # Caminho absoluto robusto para o ficheiro de mensagens de agradecimento
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    thanks_path = os.path.join(BASE_DIR, "informations", "thanksmessages.json")
    print("Vou abrir:", thanks_path)
    print("File exists?", os.path.isfile(thanks_path))
    with open(thanks_path, "r", encoding="utf-8") as f:
        THANKS_MESSAGES = json.load(f)

    fb_collection = client.assistente_cozinha.feedback
    def blocking_watch():
        with fb_collection.watch() as stream:
            for change in stream:
                if change["operationType"] == "insert":
                    print("[MongoDB] Novo feedback inserido:", change["fullDocument"])
                    thanks_msg = random.choice(THANKS_MESSAGES)
                    if event_loop:
                        asyncio.run_coroutine_threadsafe(message_queue.put(thanks_msg), event_loop)

    await asyncio.to_thread(blocking_watch)

async def websocket_main():
    print("Servidor WebSocket iniciado na porta 8765 (APP) e 8005 (ASSESSMENT)")
    # Servidor para APP (já existente)
    server_app = await websockets.serve(websocket_handler, "localhost", 8765)
    # Novo servidor para ASSESSMENT
    ssl_context = ssl._create_unverified_context()
    async def assessment_handler(websocket):
        print("Novo cliente WebSocket conectado em /ASSESSMENT.")
        try:
            async for message in websocket:
                try:
                    # Tenta decodificar mensagem (caso venha codificada em hex)
                    try:
                        message = bytes.fromhex(message).decode("utf-8")
                        print(message)
                    except:
                        pass
                    print(f"[ASSESSMENT WS] Mensagem recebida: {message}")
                    # Aqui podes processar a mensagem recebida do SCXML
                except Exception as e:
                    print(f"[ASSESSMENT WS] Erro ao processar mensagem recebida: {e}")
        except websockets.exceptions.ConnectionClosed:
            print("Cliente WebSocket desconectado de /ASSESSMENT.")

    # Serve o endpoint wss://localhost:8010/IM/USER1/ASSESSMENT
    server_assessment = await websockets.serve(
        assessment_handler, "localhost", 8010, ssl=ssl_context
    )

    try:
        await asyncio.gather(
            notify_clients(),      # Corre o loop que envia mensagens da queue
            watch_feedback_logs(),  # Escuta os logs de feedback
            server_app.wait_closed(),
            server_assessment.wait_closed()
        )
    except Exception as e:
        print(f"[WebSocket] Erro: {e}")
    



# -------------------------------
# Enviar evento SCXML externo
# -------------------------------
async def send_scxml_event(event_name):
    try:
        uri = "wss://localhost:8005/IM/USER1/APP"
        ssl_context = ssl._create_unverified_context()

        event_command = event_name.replace("mmi:", "")  # e.g. "feedbackStart"
        message = f"""
        <mmi:mmi xmlns:mmi="http://www.w3.org/2008/04/mmi-arch">
            <mmi:extensionNotification mmi:context="ctx-1" mmi:requestId="req-1" mmi:source="ASSESSMENT" mmi:target="IM">
                <mmi:data>
                    <event>{event_command}</event>
                </mmi:data>
            </mmi:extensionNotification>
        </mmi:mmi>
        """

        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            await websocket.send(message)
            print(f"[SCXML] Enviado mmi:extensionNotification com evento: {event_name}")
    except Exception as e:
        print(f"[SCXML] Erro ao enviar evento {event_name}: {e}")

def trigger_scxml_event(event_name):
    if event_loop:
        asyncio.run_coroutine_threadsafe(send_scxml_event(event_name), event_loop)
    else:
        print("[SCXML] event_loop não definido.")


# -------------------------------
# Flask rotas
# -------------------------------
@app.route("/evaluate", methods=["POST"])
def evaluate():
    log_data = request.json
    print("Recebido no /evaluate:", log_data)
    if not log_data or "intent" not in log_data:
        return jsonify({"error": "Dados inválidos"}), 400

    intent = log_data["intent"]
    return send_message(intent)

@app.route("/feedback/state", methods=["GET", "POST"])
def set_feedback_state():

    if request.method == "GET":
        state = feedback_state_collection.find_one({"_id": "feedback_state"})
        return jsonify({"feedback_state": state.get("state", "inactive")})
    
    data = request.json
    new_state = data.get("state", "inactive")
    feedback_state_collection.update_one(
        {"_id": "feedback_state"},
        {"$set": {"state": new_state}},
        upsert=True
    )
    if new_state == "active":
        trigger_scxml_event("mmi:feedbackStart")
        print("Estou na route")
    elif new_state == "inactive":
        trigger_scxml_event("mmi:feedbackStop")
    return jsonify({"feedback_state": new_state}), 200

@app.route('/feedback/receive', methods=['POST'])
def receive_feedback():
    data = request.json
    timestamp = datetime.now().isoformat()

    # Vai buscar a última pergunta feita
    question_doc = db.question.find_one({"_id": "last"}) or {}
    related_intent = question_doc.get("intent", "unknown")
    question_type = question_doc.get("question_type", "unknown")
    question_text = question_doc.get("question", "")

    # Marcar como feedback válido
    log_entry = {
        'timestamp': timestamp,
        'from_feedback': True,
        'text': data.get('text'),
        'intent': "feedback",
        'related_intent': related_intent,
        'question_type': question_type,
        'question': question_text,
        'utilizador_id': current_user.get("user_id"),
        'utilizador_nome': current_user.get("nome"),
        'raw': data  # opcional, guarda tudo o que veio
    }

    fb_collection = client.assistente_cozinha.feedback
    fb_collection.insert_one(log_entry)
    print("[Feedback] Feedback guardado na BD:", log_entry)

    feedback_state_collection.update_one(
        {"_id": "feedback_state"},
        {"$set": {"state": "inactive"}},
        upsert=True
    )
    trigger_scxml_event("mmi:feedbackStop") 

    return jsonify({'status': 'feedback received'}), 200

# -------------------------------
# Envio da Mensagem via WebSocket
# -------------------------------
def send_message(intent):
    feedback_state_collection.update_one(
        {"_id": "feedback_state"},
        {"$set": {"state": "active"}},
        upsert=True
    )
    print("Estado de feedback ativado.")

    # Ativar estado de feedback no SCXML
    trigger_scxml_event("mmi:feedbackStart")
    print("Estou na send_message")

    with open("informations/kitchenQuestions.json", "r", encoding="utf-8") as file:
        feedback_data = json.load(file)

        # Verifica se o intent existe no JSON
        if intent not in feedback_data:
            return jsonify({"error": "Intent não encontrado no JSON"}), 404

        # Seleciona aleatoriamente entre yes_no_questions e scale_questions
        available_types = [qt for qt in ["yes_no_questions", "scale_questions"] if feedback_data[intent].get(qt)]
        if not available_types:
            return jsonify({"error": "Sem perguntas disponíveis para este intent."}), 404

        question_type = random.choice(available_types)
        questions = feedback_data[intent][question_type]

        if not questions:
            return jsonify({"error": f"Sem perguntas disponíveis para {question_type}"}), 404

        # Seleciona uma pergunta aleatória do tipo escolhido
        message = random.choice(questions)

        db.question.update_one(
            {"_id": "last"},
            {"$set": {
                "intent": intent,
                "question_type": question_type,
                "question": message
            }},
            upsert=True
        )

    global event_loop
    if event_loop:
        asyncio.run_coroutine_threadsafe(message_queue.put(message), event_loop)
    else:
        print("Erro: event_loop ainda não foi definido.")

    return jsonify({"status": "Mensagem enviada", "question_type": question_type, "message": message}), 200
# -------------------------------
# Inicialização
# -------------------------------
def start_flask():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("AssessmentManager")
    logger.info("Assessment Manager iniciado. Servidor Flask em http://localhost:5002")
    app.run(port=5002, use_reloader=False)  # use_reloader=False evita conflitos com o loop

if __name__ == "__main__":
    event_loop = asyncio.get_event_loop()  # <- Define o loop global

    # Inicia o servidor Flask em thread separada
    import threading
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # Roda o servidor WebSocket no loop principal
    event_loop.run_until_complete(websocket_main())