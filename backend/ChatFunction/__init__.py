import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ConnectionType
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI

# Chargement des variables d'environnement (.env)
load_dotenv()

# — Configuration Azure AI Foundry & Search —
project = AIProjectClient.from_connection_string(
    conn_str=os.getenv("AIPROJECT_CONNECTION_STRING"),
    credential=DefaultAzureCredential()
)
# Récupère la connexion Azure Cognitive Search provisionnée par Foundry
search_conn = project.connections.get_default(
    connection_type=ConnectionType.AZURE_AI_SEARCH,
    include_credentials=True
)
search_client = SearchClient(
    endpoint=search_conn.endpoint_url,
    index_name=os.getenv("AISEARCH_INDEX_NAME"),
    credential=AzureKeyCredential(search_conn.key)
)
# Client embeddings pour transformer les requêtes en vecteurs
embed_client = project.inference.get_embeddings_client()

# — Configuration Azure OpenAI —
openai_client = AzureOpenAI(
    api_version=os.getenv("API_VERSION"),
    azure_endpoint=os.getenv("ENDPOINT"),
    api_key=os.getenv("SUBSCRIPTION_KEY")
)
deployment = os.getenv("DEPLOYMENT")  # nom du déploiement GPT
default_model = deployment


def retrieve_documents(query: str, top_k: int = 5) -> list[dict]:
    """
    Exécute une recherche vectorielle sur l'index existant et renvoie les documents.
    """
    # Génération de l'embedding
    emb = embed_client.embed(
        model=os.getenv("EMBEDDINGS_MODEL"),
        input=query
    )
    vector = emb.data[0].embedding

    # Recherche vectorielle
    vq = VectorizedQuery(
        vector=vector,
        k_nearest_neighbors=top_k,
        fields=os.getenv("EMBEDDING_FIELD", "contentVector")
    )
    results = search_client.search(
        search_text="",
        vector_queries=[vq],
        select=["id", "nom", "groupe_musculaire", "description"]
    )
    docs = []
    for r in results:
        docs.append({
            "id": r["id"],
            "nom": r.get("nom"),
            "groupe_musculaire": r.get("groupe_musculaire"),
            "description": r.get("description"),
        })
    return docs


def build_prompt(docs: list[dict], user_query: str) -> list[dict]:
    """
    Construit la liste de messages pour l'appel Chat completions, 
    en intégrant les docs récupérées et la requête utilisateur.
    """
    system_content = (
        "Tu es SpotterCopilot, un coach de musculation IA. "
        "Tu ne réponds qu'à des questions sportives et tu utilises les exercices fournis pour construire ta réponse.\n"
        "Exercices pertinents :\n"
    )
    for d in docs:
        system_content += f"- {d['nom']} ({d['groupe_musculaire']}): {d['description']}\n"
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_query}
    ]
    return messages


def chat_with_rag(user_input: str) -> str:
    """
    Pipeline RAG complet : retrieve -> prompt -> chat -> réponse texte
    """
    docs = retrieve_documents(user_input)
    messages = build_prompt(docs, user_input)
    response = openai_client.chat.completions.create(
        messages=messages,
        model=default_model,
        max_tokens=800,
        temperature=0.7
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    print("🏋️  SpotterCopilot RAG démarré (EXIT pour quitter)")
    while True:
        q = input("🧑> ")
        if q.strip().lower() in ("exit", "quit"):
            break
        try:
            answer = chat_with_rag(q)
            print("\n🤖", answer, "\n")
        except Exception as e:
            print("Erreur : ", e)
            break
