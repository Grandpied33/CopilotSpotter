import os, json
import azure.functions as func
from dotenv import load_dotenv
from openai import AzureOpenAI
from backend.chat.retrieve_docs import retrieve_docs

load_dotenv()

# Initialisation OpenAI client
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
            return func.HttpResponse("Champ 'user_input' manquant", status_code=400)

        docs = retrieve_docs(user_input=user_input)
        context = "\n\n".join([d.get("content", "") for d in docs])

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
                "content": user_input,
            }
        ],

        response = client.chat.completions.create(
            model=os.getenv("DEPLOYMENT"),
            messages=messages,
            temperature=0.7,
            max_tokens=700
        )

        assistant_reply = response.choices[0].message.content.strip()
        return func.HttpResponse(json.dumps({"assistant_response": assistant_reply}), mimetype="application/json")


    except Exception as e:

        import traceback

        return func.HttpResponse(

            f"Erreur 500:\n{str(e)}\n\nTrace:\n{traceback.format_exc()}",

            status_code=500

        )