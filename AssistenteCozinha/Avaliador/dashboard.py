from flask import Flask, jsonify, request, session, redirect, url_for, send_from_directory
from pymongo import MongoClient
from flask_cors import CORS
from pymongo.server_api import ServerApi
from werkzeug.security import generate_password_hash, check_password_hash
from collections import defaultdict
from datetime import datetime
from informations.metric_questions import metric_questions
from informations.tasks_metrics import tasks_metrics
import re
import os
import csv
import unicodedata

# Configuração do MongoDB
uri = "mongodb+srv://PECI:evaluation@peci.ss2x5.mongodb.net/?retryWrites=true&w=majority&appName=PECI"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.assistente_cozinha
feedback_collection = db.feedback
users_collection = client.assessment_db.users

# Configuração do Flask
app = Flask(__name__)
app.secret_key = "super-secret-key"
CORS(app)

#rota login
@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.json
        user = users_collection.find_one({"username": data["username"]})

        if user and check_password_hash(user["password"], data["password"]):
            session["user"] = user["username"]
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Usuário ou senha inválidos"}), 401
    except Exception as e:
        print("Erro no login:", e)
        return jsonify({"success": False, "message": "Erro interno no servidor"}), 500

#rota para logout
@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"success": True})

#rota para login page
@app.route("/login", methods=["GET"])
def login_page():
    return send_from_directory("static", "login.html")

# Middleware para proteger a dashboard
@app.before_request
def check_authentication():
    # Corrigido: Adicionada vírgula entre os caminhos protegidos
    protected_paths = ["/metrics", "/api/metrics", "/api/justificacoes"]
    if any(request.path.startswith(path) for path in protected_paths) and "user" not in session:
        return redirect(url_for("login_page"))

# Mapeamento de intents para métricas principais
intent_to_metric = {
    # Estes nomes de intent devem corresponder aos definidos no nlu.yml
    'feedback_facil_de_usar': 'facil_de_usar',
    'feedback_estou_satisfeito': 'estou_satisfeito',
    'feedback_usaria_novamente': 'usaria_novamente',
    'feedback_comunica_bem': 'comunica_bem',
    'feedback_faz_oque_quero': 'faz_oque_quero',
    # Adicione outros intents relevantes se necessário
}

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    try:
        print("Fetching metrics from database...")
        feedbacks = list(feedback_collection.find({"$or": [
            {"intent": {"$exists": True}},
            {"question": {"$exists": True}}
        ]}, {"_id": 0, "intent": 1, "question": 1, "resposta": 1, "text": 1, "utilizador_nome": 1}))
        print(f"Feedbacks fetched: {len(feedbacks)}")

        def normalize_question(q):
            if not q:
                return ""
            q = str(q).strip().lower()
            q = ''.join(c for c in unicodedata.normalize('NFD', q) if unicodedata.category(c) != 'Mn')
            q = re.sub(r'[^a-z0-9 ]', '', q)
            q = re.sub(r'\s+', ' ', q)
            return q

        question_to_metric = {}
        for metric, questions in metric_questions.items():
            for q in questions:
                question_to_metric[normalize_question(q)] = metric

        def normalize_answer(ans):
            if not ans:
                return None
            ans = str(ans).strip().lower()
            extenso = {"zero": 0, "um": 1, "uma": 1, "dois": 2, "duas": 2, "três": 3, "quatro": 4, "cinco": 5}
            # Aceitar extenso apenas se a resposta for exatamente ou repetições dessas palavras
            palavras = ans.split()
            if all(p in extenso for p in palavras) and 1 <= len(palavras) <= 3:
                # Se todas as palavras são extenso, pegar o valor da primeira
                return extenso[palavras[0]]
            if ans in extenso:
                return extenso[ans]
            if ans in ["1", "2", "3", "4", "5", "0"]:
                return int(ans)
            # Procurar o primeiro número de 1 a 5 na resposta
            match = re.search(r"[1-5]", ans)
            if match:
                return int(match.group(0))
            positivas = ["sim", "consegui", "consigo", "percebi", "claro", "afirmativo", "positivo", "yes"]
            negativas = ["não", "nao", "não consegui", "não percebi", "nao consegui", "negativo", "nunca", "no"]
            if any(p in ans for p in positivas):
                return 5
            if any(n in ans for n in negativas):
                return 0
            return None

        metric_sum = {m: 0 for m in metric_questions}
        metric_count = {m: 0 for m in metric_questions}
        debug_rows = []

        user_filter = request.args.get("user")
        utilizadores = set()
        for fb in feedbacks:
            utilizador_nome = fb.get("utilizador_nome", "")
            utilizadores.add(utilizador_nome)
            if user_filter and utilizador_nome != user_filter:
                continue
            # Preferir intent, fallback para question
            intent = fb.get("intent")
            metric = None
            if intent and intent in intent_to_metric:
                metric = intent_to_metric[intent]
            else:
                q = fb.get("question", "")
                metric = question_to_metric.get(normalize_question(q))
            resposta_val = fb.get("resposta") if fb.get("resposta") is not None else fb.get("text")
            val = normalize_answer(resposta_val)
            if metric and val is not None:
                metric_sum[metric] += val
                metric_count[metric] += 1
            debug_rows.append({
                "intent": intent if intent else "",
                "question": fb.get("question", ""),
                "resposta": resposta_val if resposta_val is not None else "",
                "metrica": metric if metric else "",
                "valor_normalizado": val if val is not None else "",
                "utilizador_nome": utilizador_nome
            })

        # Garantir que o diretório existe
        debug_path = os.path.join(os.path.dirname(__file__), "debug_feedback_metrics.csv")
        quant_path = os.path.join(os.path.dirname(__file__), "debug_feedback_metrics_quantificaveis.csv")
        with open(debug_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["intent", "question", "resposta", "metrica", "valor_normalizado", "utilizador_nome"])
            writer.writeheader()
            for row in debug_rows:
                writer.writerow(row)
        # Escrever apenas respostas quantificáveis (0-5)
        with open(quant_path, "w", encoding="utf-8", newline="") as f2:
            writer2 = csv.DictWriter(f2, fieldnames=["intent", "question", "resposta", "metrica", "valor_normalizado", "utilizador_nome"])
            writer2.writeheader()
            for row in debug_rows:
                try:
                    v = float(row["valor_normalizado"])
                    if 0 <= v <= 5:
                        writer2.writerow(row)
                except Exception:
                    continue
        # Escrever respostas não quantificáveis
        nao_quant_path = os.path.join(os.path.dirname(__file__), "debug_feedback_metrics_nao_quantificaveis.csv")
        with open(nao_quant_path, "w", encoding="utf-8", newline="") as f3:
            writer3 = csv.DictWriter(f3, fieldnames=["intent", "question", "resposta", "metrica", "valor_normalizado", "utilizador_nome"])
            writer3.writeheader()
            for row in debug_rows:
                if row["valor_normalizado"] == "":
                    writer3.writerow(row)

        metric_percent = {}
        for m in metric_questions:
            if metric_count[m] > 0:
                metric_percent[m] = round((metric_sum[m] / metric_count[m]) / 5 * 100, 2)
            else:
                metric_percent[m] = 0.0

        return jsonify(metric_percent)
    except Exception as e:
        print("Error in /api/metrics:", e)
        return jsonify({"error": "Internal Server Error"}), 500

@app.route("/metrics", methods=["GET"])
def metrics_page():
    return send_from_directory("static", "scores.html")

@app.route("/api/justificacoes", methods=["GET"])
def get_justificacoes():
    feedbacks = list(
        feedback_collection.find(
            {},  # Todos os feedbacks
            {"_id": 0, "timestamp": 1, "utilizador_nome": 1, "question": 1, "pergunta": 1, "resposta": 1, "text": 1}
        )
    )
    # Normalizar campos para garantir compatibilidade com o frontend
    result = []
    for fb in feedbacks:
        pergunta = fb.get("pergunta") or fb.get("question") or ""
        resposta = fb.get("resposta") if fb.get("resposta") is not None else fb.get("text", "")
        result.append({
            "timestamp": fb.get("timestamp", ""),
            "utilizador": fb.get("utilizador_nome", ""),
            "pergunta": pergunta,
            "resposta": resposta
        })
    return jsonify(result)

@app.route("/api/task_metrics", methods=["GET"])
def get_task_metrics():
    try:
        feedbacks = list(feedback_collection.find({"question": {"$exists": True}}, {"_id": 0, "question": 1, "resposta": 1, "text": 1, "timestamp": 1}))
        def normalize_question(q):
            if not q:
                return ""
            q = str(q).strip().lower()
            q = ''.join(c for c in unicodedata.normalize('NFD', q) if unicodedata.category(c) != 'Mn')
            q = re.sub(r'[^a-z0-9 ]', '', q)
            q = re.sub(r'\s+', ' ', q)
            return q
        question_to_task = {}
        for task, questions in tasks_metrics.items():
            for q in questions:
                question_to_task[normalize_question(q)] = task
        def normalize_answer(ans):
            if not ans:
                return None
            ans = str(ans).strip().lower()
            extenso = {"zero": 0, "um ": 1, "dois": 2, "três": 3, "quatro": 4, "cinco": 5}
            for palavra, valor in extenso.items():
                if palavra in ans:
                    return valor
            match = re.search(r"[0-5]", ans)
            if match:
                return int(match.group(0))
            if any(x in ans for x in ["sim", "consegui", "consigo", "percebi", "claro", "afirmativo", "positivo", "yes"]):
                return 5
            if any(x in ans for x in ["não", "nao", "não consegui", "não percebi", "nao consegui", "negativo", "nunca", "no"]):
                return 0
            return None
        from collections import defaultdict
        import datetime
        day_task_values = defaultdict(lambda: defaultdict(list))
        debug_rows = []
        for fb in feedbacks:
            q = fb.get("question", "")
            task = question_to_task.get(normalize_question(q))
            if not task:
                continue
            resposta_val = fb.get("resposta") if fb.get("resposta") is not None else fb.get("text")
            val = normalize_answer(resposta_val)
            if val is None:
                continue
            ts = fb.get("timestamp")
            if ts:
                try:
                    dt = datetime.datetime.fromisoformat(ts[:19])
                    day_key = dt.strftime("%Y-%m-%d")
                except Exception:
                    day_key = "sem_data"
            else:
                day_key = "sem_data"
            day_task_values[day_key][task].append(val)
            debug_rows.append({
                "pergunta": q,
                "tipo_de_tarefa": task,
                "score": val
            })
        # Escrever CSV de debug
        debug_path = os.path.join(os.path.dirname(__file__), "debug_task_metrics.csv")
        with open(debug_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["pergunta", "tipo_de_tarefa", "score"])
            writer.writeheader()
            for row in debug_rows:
                writer.writerow(row)
        # Calcular médias diárias por tarefa
        result = {}
        for day in sorted(day_task_values.keys()):
            result[day] = {}
            for task in ["gestao_despensa", "receitas", "lista_compras"]:
                vals = day_task_values[day][task]
                result[day][task] = round(sum(vals)/len(vals), 2) if vals else None
        return jsonify(result)
    except Exception as e:
        print("Error in /api/task_metrics:", e)
        return jsonify({"error": "Internal Server Error"}), 500

@app.route("/api/metrics_raw", methods=["GET"])
def get_metrics_raw():
    """
    Retorna os valores individuais normalizados de cada feedback por métrica,
    para alimentar o swarmplot/violinplot no frontend, incluindo perguntas e respostas.
    """
    try:
        feedbacks = list(feedback_collection.find({"$or": [
            {"intent": {"$exists": True}},
            {"question": {"$exists": True}}
        ]}, {"_id": 0, "intent": 1, "question": 1, "resposta": 1, "text": 1, "utilizador_nome": 1}))
        intent_to_metric = {
            'feedback_facil_de_usar': 'facil_de_usar',
            'feedback_estou_satisfeito': 'estou_satisfeito',
            'feedback_usaria_novamente': 'usaria_novamente',
            'feedback_comunica_bem': 'comunica_bem',
            'feedback_faz_oque_quero': 'faz_oque_quero',
        }
        import unicodedata
        def normalize_question(q):
            if not q:
                return ""
            q = str(q).strip().lower()
            q = ''.join(c for c in unicodedata.normalize('NFD', q) if unicodedata.category(c) != 'Mn')
            q = re.sub(r'[^a-z0-9 ]', '', q)
            q = re.sub(r'\s+', ' ', q)
            return q
        question_to_metric = {}
        for metric, questions in metric_questions.items():
            for q in questions:
                question_to_metric[normalize_question(q)] = metric
        def normalize_answer(ans):
            if not ans:
                return None
            ans = str(ans).strip().lower()
            # Aceitar apenas respostas exatas (não frases)
            extenso = {"zero": 0, "um": 1, "uma": 1, "dois": 2, "duas": 2, "três": 3, "quatro": 4, "cinco": 5}
            if ans in extenso:
                return extenso[ans]
            if ans in ["1", "2", "3", "4", "5", "0"]:
                return int(ans)
            # Procurar o primeiro número de 1 a 5 na resposta
            match = re.search(r"[1-5]", ans)
            if match:
                return int(match.group(0))
            return None
        # Coletar respostas individuais por métrica, perguntas e respostas
        metric_values = {m: [] for m in metric_questions}
        metric_perguntas = {m: [] for m in metric_questions}
        metric_respostas = {m: [] for m in metric_questions}
        user_filter = request.args.get("user")
        utilizadores = set()
        for fb in feedbacks:
            utilizador_nome = fb.get("utilizador_nome", "")
            utilizadores.add(utilizador_nome)
            if user_filter and utilizador_nome != user_filter:
                continue
            intent = fb.get("intent")
            metric = None
            if intent and intent in intent_to_metric:
                metric = intent_to_metric[intent]
            else:
                q = fb.get("question", "")
                metric = question_to_metric.get(normalize_question(q))
            resposta_val = fb.get("resposta") if fb.get("resposta") is not None else fb.get("text")
            val = normalize_answer(resposta_val)
            if metric and val is not None:
                metric_values[metric].append(val)
                metric_perguntas[metric].append(fb.get("question", ""))
                metric_respostas[metric].append(resposta_val if resposta_val is not None else "")
        # Montar resposta
        result = {}
        for m in metric_questions:
            result[m] = metric_values[m]
            result[f"{m}_perguntas"] = metric_perguntas[m]
            result[f"{m}_respostas"] = metric_respostas[m]
        return jsonify(result)
    except Exception as e:
        print("Error in /api/metrics_raw:", e)
        return jsonify({"error": "Internal Server Error"}), 500

@app.route("/api/users", methods=["GET"])
def get_users():
    feedbacks = list(feedback_collection.find({}, {"_id": 0, "utilizador_nome": 1}))
    users = sorted(set(fb.get("utilizador_nome", "") for fb in feedbacks if fb.get("utilizador_nome")))
    return jsonify(["Todos"] + users)

if __name__ == "__main__":
    app.run(port=5003, debug=True)