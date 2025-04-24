import os, json
import azure.functions as func
from openai import AzureOpenAI
from dotenv import load_dotenv
from retrieve_docs import get_product_documents 

load_dotenv()

# Init Azure OpenAI client
client = AzureOpenAI(
    api_version=os.getenv("API_VERSION"),
    azure_endpoint=os.getenv("ENDPOINT"),
    api_key=os.getenv("SUBSCRIPTION_KEY"),
)

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        user_input = body.get("user_input", "")
        
        # 1. Récupération des documents
        docs = get_product_documents([{"role": "user", "content": user_input}], {})
        context = "\n".join([doc["text"] for doc in docs]) if docs else "Aucun document trouvé."

        # 2. Génération du message avec contexte
        messages = [
            {
                "role": "system",
                "content": (
                    "Tu es SpotterCopilot, un assistant d'entraînement sportif. Tu réponds uniquement aux questions "
                    "liées au sport, à la musculation, au fitness ou à la récupération. Voici des extraits utiles :\n"
                    f"{context}"
                )
            },
            {
                "role": "user",
                "content": user_input
            }
        ]

        # 3. Appel à l'API OpenAI
        resp = client.chat.completions.create(
            model=os.getenv("DEPLOYMENT"),
            messages=messages,
            temperature=0.8,
            max_tokens=600
        )
        answer = resp.choices[0].message.content

        return func.HttpResponse(
            json.dumps({"assistant_response": answer}),
            mimetype="application/json", status_code=200
        )

    except Exception as e:
        return func.HttpResponse(f"Erreur serveur : {str(e)}", status_code=500)
