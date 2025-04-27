# chat/__init__.py
import os
import json
import logging

import azure.functions as func
from openai import AzureOpenAI
from dotenv import load_dotenv
from .retrieve_docs import retrieve_docs
from azure.data.tables import TableServiceClient

load_dotenv()

client = AzureOpenAI(
    api_key        = os.getenv("SUBSCRIPTION_KEY"),
    azure_endpoint = os.getenv("ENDPOINT"),
    api_version    = os.getenv("API_VERSION")
)

# table pour l’historique des poids
table = TableServiceClient.from_connection_string(
    os.getenv("AZURE_TABLE_CONN")
).get_table_client(table_name="UserProgress")

def load_history(user_id):
    try:
        ent = table.get_entity(partition_key=user_id, row_key="history")
        return json.loads(ent["Weights"])
    except:
        return {}

def save_history(user_id, history):
    table.upsert_entity({
        "PartitionKey": user_id,
        "RowKey":       "history",
        "Weights":      json.dumps(history)
    })

SYSTEM_PROMPT = """
Tu es SpotterCopilot, coach IA expert en musculation et en sport.
Tu réponds uniquement aux questions liées au sport, à la nutrition sportive et à la santé physique.
Si l’utilisateur mentionne un groupe musculaire (ex. “biceps”, “jambes”, “pecs”…) et une durée en minutes (ex. “20 minutes”, “45 min”), tu considères que tu as toutes les infos nécessaires et tu génères immédiatement un programme détaillé (échauffement, exercices, séries, répétitions, charge estimée, repos).
Après le programme, tu invites l’utilisateur à envoyer son feedback de séance (ex. “feedback: 4×10 @20kg — facile”).
Si l’utilisateur envoie un feedback, tu ajustes les charges pour la prochaine séance.
Refuse poliment toute demande hors sport et nutrition (code, amour, finance…).
"""

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body      = req.get_json()
        user_input= body.get("user_input","").strip()
        user_id   = req.headers.get("X-User-Id","default")

        if not user_input:
            return func.HttpResponse(
                json.dumps({"error":"Champ 'user_input' manquant"}),
                status_code=400, mimetype="application/json"
            )

        # charge l'historique
        history = load_history(user_id)
        histo_text = "\n".join(f"- {e}: {w} kg" for e,w in history.items())

        # contexte RAG
        docs = retrieve_docs(user_input)
        ctx  = "\n\n".join(d["content"] for d in docs)

        # construit messages
        messages = [{"role":"system","content":SYSTEM_PROMPT}]
        if histo_text:
            messages.append({"role":"system","content":"Historique des poids :\n" + histo_text})
        if ctx:
            messages.append({"role":"system","content":"Contexte pertinent :\n" + ctx})
        messages.append({"role":"user","content":user_input})

        # appel OpenAI
        resp = client.chat.completions.create(
            model                 = os.getenv("DEPLOYMENT"),
            messages              = messages,
            top_p                 = 1.0,
            max_completion_tokens = 1000
        )
        answer = resp.choices[0].message.content.strip()

        # sauvegarde JSON weights si l'IA en retourne
        try:
            parsed = json.loads(answer)
            if isinstance(parsed, dict) and parsed.get("weights"):
                history.update(parsed["weights"])
                save_history(user_id, history)
        except:
            pass

        return func.HttpResponse(answer, status_code=200)

    except Exception as e:
        logging.exception("Erreur inattendue")
        return func.HttpResponse("Une erreur interne est survenue.", status_code=500)
