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
        # 1) récupère les docs pertinents
        docs = get_product_documents([{"role":"user","content":user_input}],{})
        # 2) génère la réponse
        messages = [
          {"role":"system","content":(
             "Tu es SpotterCopilot… Tu ne réponds qu’au sport.")},
          {"role":"assistant","content":""},  # placeholder
          {"role":"user","content": user_input}
        ]
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
        return func.HttpResponse(str(e), status_code=500)
