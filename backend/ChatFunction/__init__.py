import os, json
import azure.functions as func
from openai import AzureOpenAI
from dotenv import load_dotenv
from .retrieve_docs import retrieve_docs  # ← Import corrigé

load_dotenv()

client = AzureOpenAI(
    api_version=os.getenv("API_VERSION"),
    azure_endpoint=os.getenv("ENDPOINT"),
    api_key=os.getenv("SUBSCRIPTION_KEY"),
)

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        user_input = body.get("user_input", "")

        docs = retrieve_docs(user_input)  # ← Appel corrigé
        context = "\n".join([d["description"] for d in docs])

        messages = [
            {"role": "system", "content": (
                "Tu es SpotterCopilot, assistant IA muscu. "
                "Tu réponds uniquement à des questions liées au sport. "
                "Voici les documents récupérés :\n" + context
            )},
            {"role": "user", "content": user_input}
        ]

        response = client.chat.completions.create(
            model=os.getenv("DEPLOYMENT"),
            messages=messages,
            temperature=0.8,
            max_tokens=600
        )

        answer = response.choices[0].message.content
        return func.HttpResponse(json.dumps({"assistant_response": answer}), mimetype="application/json")

    except Exception as e:
    print(f"🔥 ERREUR: {e}")
    return func.HttpResponse(str(e), status_code=500)

