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

SYSTEM_PROMPT = """
Tu es SpotterCopilot, un coach IA expert en musculation.
Quand l’utilisateur demande un entraînement (ex. “je veux m’entraîner les bras”), tu dois :
1) Lui demander son état de forme du jour (en forme / normal / fatigué).
2) Lui demander la durée dont il dispose pour sa séance (en minutes).
3) Proposer un programme détaillé adapté (exercices, séries, répétitions, charges estimées, repos).
4) Une fois le programme envoyé, inviter l’utilisateur à faire son retour de séance en lui demandant :
   - Pour chaque exercice, combien de séries as-tu fait ?
   - Combien de répétitions ?
   - À quel poids pour chaque série ?
   - Comment tu t’es senti (facile / difficile) ?
Répond toujours au format JSON avec au moins les clés "programme" (liste d’exos) et "next_step" (phrase de suivi).
"""

FB_PROMPT = """
Tu es SpotterCopilot.
L’utilisateur t’a renvoyé son feedback de séance sous forme :
Exercice A : 4 séries de 10 @ 22kg (difficile)
Exercice B : 3 séries de 12 @ 14kg (facile)
Lis ce feedback et renvoie un JSON :
{
  "feedback_ack": "<message d’encouragement>",
  "adjustments": {
    "Exercice A": {"ajustement": "+2kg", "nouveau_target": "10-12"},
    "Exercice B": {"ajustement": "-2kg", "nouveau_target": "12-15"}
  }
}
"""

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body        = req.get_json()
        user_input  = body.get("user_input", "").strip()
        memory      = body.get("memory", "").strip()
        is_feedback = body.get("feedback", False)

        if not user_input:
            return func.HttpResponse(
                json.dumps({"error": "Champ 'user_input' manquant"}),
                status_code=400, mimetype="application/json"
            )

        if not is_feedback:
            # 1) Récupération des docs (RAG) et construction du prompt
            docs    = retrieve_docs(user_input)
            context = "\n\n".join(d.get("content", "") for d in docs)

            prompt = SYSTEM_PROMPT
            if memory:
                prompt += "\nHistorique des poids :\n" + memory
            if context:
                prompt += "\n\nContexte additionnel :\n" + context

            max_tokens = 2000
        else:
            # 2) Mode feedback
            prompt     = FB_PROMPT + "\nFeedback reçu :\n" + user_input
            max_tokens = 500

        # 3) Appel OpenAI
        resp = client.chat.completions.create(
            model                  = os.getenv("DEPLOYMENT"),
            messages               = [
                {"role": "system", "content": prompt},
                {"role": "user",   "content": user_input}
            ],
            top_p                  = 1.0,
            max_completion_tokens  = max_tokens
        )
        answer = resp.choices[0].message.content.strip()

        return func.HttpResponse(
            json.dumps({"assistant_response": answer}),
            status_code=200, mimetype="application/json"
        )

    except Exception:
        logging.exception("Erreur inattendue dans SpotterCopilot")
        return func.HttpResponse(
            json.dumps({"error": "Une erreur interne est survenue."}),
            status_code=500, mimetype="application/json"
        )
