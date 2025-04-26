# chat/__init__.py
import os
import json
import logging

import azure.functions as func
from openai import AzureOpenAI
from dotenv import load_dotenv
from .retrieve_docs import retrieve_docs

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("SUBSCRIPTION_KEY"),
    azure_endpoint=os.getenv("ENDPOINT"),
    api_version=os.getenv("API_VERSION")
)

SYSTEM_PROMPT = """
Tu es SpotterCopilot, un coach IA expert en musculation.
Quand l’utilisateur demande un entraînement (ex. “je veux m’entraîner les bras”), tu dois :
1) Lui demander son état de forme du jour (en forme / normal / fatigué).
2) Lui demander la durée dont il dispose pour sa séance (en minutes).
3) Proposer un programme détaillé adapté (exercices, séries, répétitions, charges estimées, repos).
4) **Une fois le programme envoyé**, inviter l’utilisateur à faire son retour de séance en lui demandant :
   - Pour chaque exercice, combien de séries as-tu fait ?
   - Combien de répétitions ?
   - À quel poids pour chaque série ?
   - Comment tu t’es senti (facile / difficile) ?
Ce retour servira à optimiser ses prochaines séances.
Répond toujours au format JSON avec au moins les clés `"programme"` (liste d’exos) et `"next_step"` qui contiendra ta question de suivi.
"""


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body       = req.get_json()
        user_input = body.get("user_input", "").strip()
        memory     = body.get("memory", "").strip()

        if not user_input:
            return func.HttpResponse(
                json.dumps({"error": "Champ 'user_input' manquant"}),
                status_code=400,
                mimetype="application/json"
            )

        # 1) récupération des docs (RAG)
        docs    = retrieve_docs(user_input)
        context = "\n\n".join(d.get("content", "") for d in docs)

        # 2) construction du prompt complet
        full_system = SYSTEM_PROMPT
        if memory:
            full_system += "\nHistorique des poids :\n" + memory
        if context:
            full_system += "\n\nContexte additionnel :\n" + context

        messages = [
            {"role": "system", "content": full_system},
            {"role": "user",   "content": user_input}
        ]

        # 3) appel OpenAI
        resp = client.chat.completions.create(
            model=os.getenv("DEPLOYMENT"),
            messages=messages,
            top_p=1.0,
            max_completion_tokens=2000
        )
        answer = resp.choices[0].message.content.strip()

        return func.HttpResponse(
            json.dumps({"assistant_response": answer}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception:
        logging.exception("Erreur inattendue dans SpotterCopilot")
        return func.HttpResponse(
            json.dumps({"error": "Une erreur interne est survenue."}),
            status_code=500,
            mimetype="application/json"
        )
