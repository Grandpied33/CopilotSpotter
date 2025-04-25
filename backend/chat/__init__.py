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
        # 1) Lecture de l’entrée
        body = req.get_json()
        user_input = body.get("user_input","").strip()
        if not user_input:
            return func.HttpResponse("Champ 'user_input' manquant", status_code=400)

        # 2) Récupération des docs
        docs = retrieve_docs(user_input)
        # 3) Construction du contexte
        context = "\n\n".join(d.get("content","") for d in docs)

        # 4) Appel OpenAI
        messages = [
            {"role":"system","content":
             "Tu es SpotterCopilot, un assistant sportif. Ne répond que sur la musculation."},
            {"role":"user","content":
             f"Contexte :\n{context}\n\nQuestion : {user_input}"}
        ]
        resp = chat_client.chat.completions.create(
            model=os.getenv("DEPLOYMENT"),
            messages=messages,
            temperature=0.7,
            max_tokens=700
        )
        answer = resp.choices[0].message.content.strip()
        return func.HttpResponse(
            json.dumps({"assistant_response": answer}),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        # Remonte la stack trace dans la réponse
        tb = traceback.format_exc()
        error_message = f"⚠️ Exception levée : {e}\n\nTraceback:\n{tb}"
        # Log dans Azure
        logging = func.logging
        logging.error(error_message)
        return func.HttpResponse(error_message, status_code=500)