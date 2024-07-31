import os
import sys
import psycopg2
import pandas as pd
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from typing import List
from geopy.distance import geodesic
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS  # Updated import
from langchain.docstore.document import Document

# Adjust sys.path to include the parent directory for importing config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config, TABLES_CONFIG

load_dotenv()

# PostgreSQL connection details
DB_HOST = Config.DB_HOST
DB_PORT = Config.DB_PORT
DB_NAME = Config.DB_NAME
DB_USER = Config.DB_USER
DB_PASSWORD = Config.DB_PASSWORD

# FAISS vector store path
VECTOR_STORE_PATH = "avathi_exp_clean_db1"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def fetch_data_from_table(table_name, fields):
    conn = get_db_connection()
    query = f'SELECT {", ".join(fields)} FROM "{table_name}" WHERE is_active = TRUE and display_priority < 5'
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def clean_html(raw_html):
    cleantext = BeautifulSoup(raw_html, "lxml").text
    return cleantext

def process_data(df, fields):
    # Ensure fields is a list
    if isinstance(fields, str):
        fields = fields.split(', ')
    
    # Define the fields you want in the metadata
    meta_fields = ['primary_key', 'name', 'location', 'display_priority', 'is_stay', 'price']
    documents = []
    
    for _, row in df.iterrows():
        # print("row:", row)
        # print("fields:", fields)
        
        content = []
        for field in fields:
            # print("field:", field)
            if field in row and pd.notnull(row[field]):
                # print("row[field]:", row[field])
                content.append(f"{field}: {row[field]}")
        
        content = "\n".join(content)
        # print("Content:", content)
        
        metadata = {}
        for field in meta_fields:
            if field in row and pd.notnull(row[field]):
                metadata[field] = row[field]
        
        # print("Metadata:", metadata)
        
        documents.append({
            'content': clean_html(content),
            'metadata': metadata
        })
    
    print("Documents:", documents)
    return documents

def create_documents_from_data(data):
    documents = []
    for item in data:
        doc = Document(
            page_content=item['content'],
            metadata=item['metadata']
        )
        documents.append(doc)
    return documents

def create_or_load_vector_store(docs, store_path=VECTOR_STORE_PATH):
    if os.path.exists(store_path):
        try:
            vector_store = FAISS.load_local(store_path, HuggingFaceEmbeddings())
            print("Loaded existing vector store.")
        except Exception as e:
            print(f"Error loading existing vector store: {e}")
            print("Creating new vector store...")
            vector_store = FAISS.from_documents(docs, HuggingFaceEmbeddings())
            vector_store.save_local(store_path)
            print("Created and saved new vector store.")
    else:
        vector_store = FAISS.from_documents(docs, HuggingFaceEmbeddings())
        vector_store.save_local(store_path)
        print("Created and saved new vector store.")
    return vector_store

def search_similar_experiences(query: str, vector_store: FAISS, k: int = 5) -> List[Document]:
    return vector_store.similarity_search(query, k=k)

def generate_response(query, context):
    llm = OpenAI(api_key=os.getenv('OPENAI_API_KEY'), temperature=0.6)
    conversation = RunnableWithMessageHistory(llm=llm, memory=ConversationBufferMemory())
    combined_info = "\n".join([doc.page_content for doc in context])
    prompt = f"User query: {query}\n\nContext:\n{combined_info}\n\nGenerate a helpful response."
    return conversation.predict(input=prompt)

def main():
    all_documents = []
    for table in TABLES_CONFIG.keys():
        df = fetch_data_from_table(table, TABLES_CONFIG[table])
        processed_data = process_data(df, TABLES_CONFIG[table])
        all_documents.extend(create_documents_from_data(processed_data))

    vector_store = create_or_load_vector_store(all_documents)

    while True:
        query = input("Ask your question: ")
        similar_experiences = search_similar_experiences(query, vector_store)
        
        print("\nSimilar experiences:")
        for doc in similar_experiences:
            print(f"Name: {doc.metadata.get('name')}")
            print(f"Location: {doc.metadata.get('location')}")
            print(f"Price: {doc.metadata.get('price')}")
            print("---")
        
        response = generate_response(query, similar_experiences)
        print(f"\nResponse: {response}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

    print("Script completed.")
    sys.exit()