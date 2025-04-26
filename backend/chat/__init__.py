# chat/__init__.py
import os
import json
import traceback
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

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        user_input = body.get("user_input", "").strip()
        if not user_input:
            return func.HttpResponse(
                json.dumps({"error": "Champ 'user_input' manquant"}),
                status_code=400,
                mimetype="application/json"
            )

        docs = retrieve_docs(user_input)
        context = "\n\n".join(d.get("content", "") for d in docs)

        messages = [
            {
                "role": "system",
                "content": (
                    "Tu es SpotterCopilot, un assistant intelligent d’entraînement sportif. "
                    "Tu aides l’utilisateur à planifier ses séances de musculation. "
                    "Tu proposes des exercices précis (avec reps, séries, charges estimées) en fonction du groupe musculaire ciblé, "
                    "de l’objectif (force, volume, endurance), et de l’état du jour (fatigué, normal, en forme). "
                    "**Tu ne réponds qu’à des sujets liés au sport, à la forme physique et à la santé.** "
                    "Si une question sort de ce cadre (informatique, météo, relations, actu…), tu dois répondre poliment que tu ne peux pas aider sur ce sujet."
                    "Sois clair, structuré, efficace."
                )
            },
            {
                "role": "user",
                "content": user_input
            }
        ]

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
