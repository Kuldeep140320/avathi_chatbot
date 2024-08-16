import os
import pandas as pd
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from bs4 import BeautifulSoup
from langchain_community.vectorstores import FAISS
from app.utils.database import get_db_connection
import sys
from typing import List, Dict, Tuple

embedding_model = "all-MiniLM-L6-v2"
instruct_embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

def clean_html(raw_html):
    """Clean HTML tags from a string."""
    if raw_html and isinstance(raw_html, str):
        cleantext = BeautifulSoup(raw_html, "lxml").text
        return cleantext.strip()
    return "N/A"

# def fetch_data_from_table(table_name: str, fields: List[str]) -> pd.DataFrame:
#     """Fetch data from the specified table in the database."""
#     conn = get_db_connection()
#     query = f'SELECT {", ".join(fields)} FROM "{table_name}" WHERE is_active = TRUE and display_priority < 20'
    
#     df = pd.read_sql(query, conn)
#     conn.close()
#     return df
def fetch_data_from_table(table_name: str) -> pd.DataFrame:
    """Fetch data from the specified table in the database."""
    conn = get_db_connection()
    query = """
    SELECT 
        e.primary_key AS eoexperience_primary_key,
        e.name AS eoexperience_name,
        e.description AS eoexperience_description,
        e.location,
        e.address,
        e.is_active AS eoexperience_is_active,
        e.is_stay,
        e.price,
        e.faqs AS eoexperience_faqs,
        e.eoproperty_primary_key,
        e.card_image_primary_key,
        e.is_choose_stay,
        e.lkdestination_primary_key,
        e.question,
        e.display_priority AS eoexperience_display_priority,
        e.expert_summery,
        e.things_to_note,
        e.things_to_do,
        e.short_name,
        e.exp_type,
        e.reviews_count,
        e.avg_rating,
        l.primary_key AS lkdestination_primary_key,
        l.name AS lkdestination_name,
        l.is_active AS lkdestination_is_active,
        p.primary_key AS eoplace_primary_key,
        p.lkdestination_primary_key AS eoplace_lkdestination_primary_key,
        p.place_title,
        p.place_description,
        p.is_active AS eoplace_is_active,
        p.faqs AS eoplace_faqs
    FROM 
        public.eoexperience e
    LEFT JOIN 
        public.lkdestination l ON e.lkdestination_primary_key = l.primary_key
    LEFT JOIN 
        public.eoplace p ON l.primary_key = p.lkdestination_primary_key
    WHERE 
        e.is_active = TRUE AND 
        l.is_active = TRUE AND 
        p.is_active = TRUE AND
        e.display_priority < 50 
    ORDER BY 
        e.primary_key ASC;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def create_documents_from_db(table_name: str, fields: List[str]) -> List[Document]:
    # print(table_name,fields)
    # sys.exit()
    df = fetch_data_from_table(table_name)
    # print(df)
    # sys.exit()
    chunk_size = 1500
    documents = []
    
    for _, row in df.iterrows():
        content = (
            f"Name: {row['eoexperience_name']}"
            # f"Location name: {clean_html(row['description'])}\n"
            # f"Name: {row['name']}"
            f"Place Title: {clean_html(row['location'])}"
            f"Description: {clean_html(row['address'])}"
            f"lkdestination_name: {row['lkdestination_name']}"
            # f"Location: {clean_html(row['price'])}"
            # f"place_title: {clean_html(row['place_title'])}\n"
            # f"Is Stay: {'Yes' if row['is_stay'] else 'No'}"
            # f"Price: {row['price'] if row['price'] else 'N/A'}"
            # f"eoexperience_faqs: {clean_html(row['eoexperience_faqs'])}\n"
            # f"expert_summery: {clean_html(row['expert_summery'])}\n"
            # f"Things to Do: {clean_html(row['things_to_do'])}\n"
            # f"Things to Note: {clean_html(row['things_to_note'])}\n"
            # f"Place Description: {clean_html(row['place_description'])}\n"
            # f"Place FAQ: {clean_html(row['eoplace_faqs'])}\n"
        )

        chunks = []
        current_chunk = ""

        for line in content.split("\n"):
            if len(current_chunk) + len(line) + 1 <= chunk_size:
                current_chunk += line + "\n"
            else:
                chunks.append(current_chunk.strip())
                current_chunk = line + "\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        display_priority = row['eoexperience_display_priority'] if pd.notnull(row['eoexperience_display_priority']) else 100

        for chunk in chunks:
            embedding = instruct_embeddings.embed_query(chunk)
            doc = Document(
                page_content=chunk,
                metadata={
                    "eoexperience_primary_key": row['eoexperience_primary_key'],
                    "eoexperience_name": row['eoexperience_name'],
                    # "lkdestination_primary_key": row['location'],
                    "lkdestination_name": row['lkdestination_name'],
                    # "eoplace_primary_key": row['eoplace_primary_key'],
                    # "eoplace_lkdestination_primary_key": row['eoplace_lkdestination_primary_key'],
                    # "eoplace_place_title": row['place_title'],
                    "display_priority": display_priority,
                    "table": "eoexperience"
                },
                embedding=embedding
            )
            # print('dd')
            # print(doc)
            # sys.exit()
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
def add_documents_to_vector_store(docs: List[Document], store_path: str):
    """Load an existing vector store, add new documents, and save it."""
    vector_store = FAISS.load_local(store_path, instruct_embeddings, allow_dangerous_deserialization=True)
    vector_store.add_documents(docs)
    vector_store.save_local(store_path)
    print("Added documents to vector store and saved it.")
    return vector_store

def initialize_vector_store(store_path):
    vector_store = FAISS.load_local(store_path, instruct_embeddings, allow_dangerous_deserialization=True)
    return {"status": "initialized", "path": vector_store}
    # return vector_store

    # table_name = "eoexperience"  # Replace with your actual table name
    # fields = ["primary_key", "name", "description", "location", "pin_code", "is_stay", "price", "latitude", "longitude", "display_priority"]
    # Create documents and vector store
    # docs = create_documents_from_db(table_name, fields)
    # vector_db_file_path = os.path.join(tempfile.gettempdir(), "vector_store_new1.db")
    # vector_db_file_path='vector_store_new1'
    # Delete the existing vector store file
    # if os.path.exists(vector_db_file_path):
        # os.remove(vector_db_file_path)
    # vector_store = initialize_vector_store(vector_db_file_path)
