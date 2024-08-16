from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from app.config import VECTOR_DB_PATH, EMBEDDING_MODEL

def initialize_vector_store():
    print(VECTOR_DB_PATH ,EMBEDDING_MODEL)
    instruct_embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vector_db = FAISS.load_local(VECTOR_DB_PATH, instruct_embeddings, allow_dangerous_deserialization=True)
    return vector_db

vector_db = initialize_vector_store()
# retriever = vector_db.as_retriever(search_kwargs={"k": 10})
retriever = vector_db.as_retriever(search_type="mmr", search_kwargs={"k": 10, "fetch_k": 50})
# retriever = vector_db.similarity_search_with_score(query,k=5, filter={"eoexperience_name": {"$exists": True}})
