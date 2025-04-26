import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("ENDPOINT")
deployment = os.getenv("DEPLOYMENT")
api_key = os.getenv("SUBSCRIPTION_KEY")
api_version = os.getenv("API_VERSION")

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=api_key,
)

print("🏋️ SpotterCopilot est prêt. Tape ce que tu veux bosser aujourd'hui ('exit' pour quitter)\n")

table_service = TableServiceClient.from_connection_string(os.getenv("AZURE_TABLE_CONN"))
table = table_service.get_table_client(table_name="UserProgress")

while True:
    user_input = input("🧑 > ")
    if user_input.lower() in ["exit", "quit"]:
        print("👋 À la prochaine séance !")
        break

    response = client.chat.completions.create(
        messages=[
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
        max_completion_tokens=1000,
        top_p=1.0,
        model=deployment
    )

    print("\n🤖 SpotterCopilot :\n")
    print(response.choices[0].message.content)
    print("\n────────────────────────────\n")
