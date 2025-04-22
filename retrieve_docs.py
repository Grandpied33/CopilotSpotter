# retrieve_docs.py
from promptflow import tool
import os
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ConnectionType
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv

load_dotenv()

# Initialise Foundry + Search
project = AIProjectClient.from_connection_string(
    conn_str=os.getenv("AIPROJECT_CONNECTION_STRING"),
    credential=DefaultAzureCredential()
)
conn = project.connections.get_default(
    connection_type=ConnectionType.AZURE_AI_SEARCH,
    include_credentials=True
)
search_client = SearchClient(
    endpoint=conn.endpoint_url,
    index_name=os.getenv("AISEARCH_INDEX_NAME"),
    credential=AzureKeyCredential(conn.key)
)
embed_client = project.inference.get_embeddings_client()

@tool
def retrieve_docs(user_input: str, top_k: int = 5) -> list:
    # Génère l’embedding de la requête
    emb = embed_client.embed(
        model=os.getenv("EMBEDDINGS_MODEL"),
        input=user_input
    )
    vec = emb.data[0].embedding

    # Lance la recherche vectorielle
    vq = VectorizedQuery(vector=vec, k_nearest_neighbors=top_k, fields="contentVector")
    results = search_client.search(search_text="", vector_queries=[vq],
                                   select=["nom", "groupe_musculaire", "description", "objectif"])
    # Formate le résultat
    docs = []
    for r in results:
        docs.append({
            "nom": r["nom"],
            "groupe_musculaire": r["groupe_musculaire"],
            "objectif": r["objectif"],
            "description": r["description"]
        })
    return docs
