import os
import pandas as pd
from typing import List
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from bs4 import BeautifulSoup
from langchain_community.vectorstores import FAISS
from app.utils.database import get_db_connection

embedding_model = "all-MiniLM-L6-v2"
instruct_embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

def clean_html(raw_html):
    """Clean HTML tags from a string."""
    cleantext = BeautifulSoup(raw_html, "lxml").text
    return cleantext

def fetch_data_from_table(table_name: str, fields: List[str]) -> pd.DataFrame:
    """Fetch data from the specified table in the database."""
    conn = get_db_connection()
    query = f'SELECT {", ".join(fields)} FROM "{table_name}" WHERE is_active = TRUE and display_priority < 5'
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def create_documents_from_db(table_name: str, fields: List[str]) -> List[Document]:
    """Create documents from database records with vector embeddings."""
    df = fetch_data_from_table(table_name, fields)
    documents = []
    for _, row in df.iterrows():
        content = f"Name: {row['name']}\n"
        content += f"Description: {clean_html(row['description'])}\n"
        content += f"Location: {row['location']}\n"
        content += f"Pin Code: {row['pin_code']}\n"
        content += f"Is Stay: {'Yes' if row['is_stay'] else 'No'}\n"
        content += f"Price: {row['price']}\n"
        content += f"Latitude: {row['latitude']}\n"
        content += f"Longitude: {row['longitude']}\n"

        # Generate vector embedding for the content
        embedding = instruct_embeddings.embed_query(content)

        doc = Document(
            page_content=content,
            metadata={
                "primary_key": row['primary_key'],
                "name": row['name'],
                "location": row['location'],
                "is_stay": row['is_stay'],
                "price": row['price'],
                "latitude": row['latitude'],
                "longitude": row['longitude'],
                "display_priority": row['display_priority']
            },
            embedding=embedding  # Store the embedding with the document
        )
        documents.append(doc)
    return documents

def create_or_load_vector_store(docs: List[Document], store_path: str):
    """Create or load a vector store with embeddings."""
    if os.path.exists(store_path):
        vector_store = FAISS.load_local(store_path, instruct_embeddings, allow_dangerous_deserialization=True)
        print("Loaded existing vector store.")
    else:
        vector_store = FAISS.from_documents(docs, instruct_embeddings)
        vector_store.save_local(store_path)
        print("Created and saved new vector store.")
    return vector_store
