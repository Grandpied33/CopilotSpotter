# chat/__init__.py
import os, json, logging
import azure.functions as func
from openai import AzureOpenAI
from dotenv import load_dotenv
from .retrieve_docs import retrieve_docs

load_dotenv()

client = AzureOpenAI(
    api_key        = os.getenv("SUBSCRIPTION_KEY"),
    azure_endpoint = os.getenv("ENDPOINT"),
    api_version    = os.getenv("API_VERSION")
)

SYSTEM_PROMPT_PROGRAM = """
Tu es SpotterCopilot, coach IA expert en musculation.
Quand l’utilisateur demande un entraînement (par ex. “je veux m’entraîner les bras”), tu dois :
1) Demander son état de forme (en forme / normal / fatigué).
2) Demander la durée dont il dispose.
3) Proposer un programme clair et détaillé :
   - Exercice : Squat
     Séries : 4
     Répétitions : 8–10
     Charge : 60 kg
     Repos : 120 s
Puis termine par : « Dis-moi quand tu as fini ta séance ! »
"""

SYSTEM_PROMPT_FEEDBACK = """
Tu es SpotterCopilot.
L’utilisateur vient de terminer sa séance et te donne son feedback, par ex. :
« Squat : 4×10 @ 60 kg — difficile  
Presse : 3×12 @ 80 kg — facile »
Analyse ce feedback et propose en texte clair comment ajuster les charges la prochaine fois.
"""

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body        = req.get_json()
        user_input  = body.get("user_input","").strip()
        memory      = body.get("memory","").strip()
        is_feedback = body.get("feedback", False)

        if not user_input:
            return func.HttpResponse(
                json.dumps({"error":"Champ 'user_input' manquant"}),
                status_code=400, mimetype="application/json"
            )

        if not is_feedback:
            docs    = retrieve_docs(user_input)
            context = "\n\n".join(d.get("content","") for d in docs)
            prompt = SYSTEM_PROMPT_PROGRAM
            if memory:
                prompt += "\nHistorique des poids :\n" + memory
            if context:
                prompt += "\n\nContexte :\n" + context
            max_tokens = 2000
        else:
            prompt = SYSTEM_PROMPT_FEEDBACK + "\nFeedback :\n" + user_input
            max_tokens = 500

        resp = client.chat.completions.create(
            model                 = os.getenv("DEPLOYMENT"),
            messages              = [
                {"role":"system","content":prompt},
                {"role":"user","content":user_input}
            ],
            top_p                 = 1.0,
            max_completion_tokens = max_tokens
        )
        answer = resp.choices[0].message.content.strip()

        return func.HttpResponse(
            json.dumps({"assistant_response": answer}),
            status_code=200, mimetype="application/json"
        )

    except Exception:
        logging.exception("Erreur inattendue")
        return func.HttpResponse(
            json.dumps({"error":"Erreur interne."}),
            status_code=500, mimetype="application/json"
        )
