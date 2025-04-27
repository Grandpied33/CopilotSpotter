import os
import json
from openai import AzureOpenAI
from dotenv import load_dotenv
from azure.data.tables import TableServiceClient
from backend.chat.retrieve_docs import retrieve_docs

load_dotenv()

client = AzureOpenAI(
    api_key        = os.getenv("SUBSCRIPTION_KEY"),
    azure_endpoint = os.getenv("ENDPOINT"),
    api_version    = os.getenv("API_VERSION")
)


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
Si l’utilisateur demande un entraînement en mentionnant un groupe musculaire et une durée en minutes, tu génères immédiatement un programme détaillé (échauffement, exercices, séries, répétitions, charge estimée, repos).
Après le programme, tu invites l’utilisateur à envoyer son feedback de séance (ex. “feedback: 4×10 @20kg — facile”).
Si l’utilisateur envoie un feedback, tu ajustes les charges pour la prochaine séance.
Refuse poliment toute demande de conseils sur le code, la programmation, les relations amoureuses, la finance ou tout autre sujet hors sport et nutrition.
"""

def main():
    user_id  = "default"
    history  = load_history(user_id)
    messages = [{"role":"system", "content": SYSTEM_PROMPT}]

    print("🏋️ SpotterCopilot CLI – tape 'exit' pour quitter.\n")

    while True:
        user_input = input("🧑 > ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("👋 À la prochaine séance !")
            break

        messages.append({"role":"user", "content": user_input})

        mem_text = "\n".join(f"- {e}: {w} kg" for e, w in history.items())
        docs = retrieve_docs(user_input)
        ctx  = "\n\n".join(d["content"] for d in docs)

        to_send = [messages[0]]
        if mem_text:
            to_send.append({"role":"system", "content": "Historique des poids :\n" + mem_text})
        if ctx:
            to_send.append({"role":"system", "content": "Contexte pertinent :\n" + ctx})
        to_send.extend(messages[1:])

        resp = client.chat.completions.create(
            model                 = os.getenv("DEPLOYMENT"),
            messages              = to_send,
            top_p                 = 1.0,
            max_completion_tokens = 2000
        )
        answer = resp.choices[0].message.content.strip()

        print("\n🤖 SpotterCopilot :\n")
        print(answer + "\n")

        messages.append({"role":"assistant", "content": answer})

        try:
            parsed = json.loads(answer)
            if isinstance(parsed, dict) and parsed.get("weights"):
                history.update(parsed["weights"])
                save_history(user_id, history)
        except:
            pass

if __name__ == "__main__":
    main()
