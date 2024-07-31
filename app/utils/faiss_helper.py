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
    query = f'SELECT {", ".join(fields)} FROM "{table_name}" WHERE is_active = TRUE and display_priority < 20'
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def create_documents_from_db(table_name: str, fields: List[str]) -> List[Document]:
    """Create documents from database records with vector embeddings."""
    df = fetch_data_from_table(table_name, fields)
    chunk_size: int = 1000
    documents = []
    for _, row in df.iterrows():
        content = f"Name: {row['name']}\n"
        content += f"Description: {clean_html(row['description'])}\n"
        content += f"Location: {row['location']}\n"
        content += f"Address: {row['address']}\n"
        content += f"Is Stay: {'Yes' if row['is_stay'] else 'No'}\n"
        content += f"Price: {row['price']}\n"
        content += f"things_to_note: {row['things_to_note']}\n"
        content += f"things_to_do: {row['things_to_do']}\n"

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
        # Generate vector embedding for the content
        embedding = instruct_embeddings.embed_query(content)
        for chunk in chunks:
            embedding = instruct_embeddings.embed_query(chunk)
            doc = Document(
                page_content=content,
                metadata={
                    "table": 'eoexperience',
                    "primary_key": row['primary_key'],
                    "name": row['name'],
                    "location": row['location'],
                    "is_stay": row['is_stay'],
                    "price": row['price'],
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
# import os
# import sys
# import tempfile
# from dotenv import load_dotenv
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from app.services.nlp import get_chain
# from app.utils.faiss_helper import create_or_load_vector_store, create_documents_from_db
# # from app.utils.faiss_helper import initialize_vector_store

# load_dotenv()
# if __name__ == "__main__":
#     table_name = "eoexperience"  # Replace with your actual table name
#     fields = ["primary_key", "name", "description", "location", "address", "is_stay", "price", "things_to_note", "things_to_do", "display_priority"]
#     # Create documents and vector store
#     docs = create_documents_from_db(table_name, fields)
#     # print(docs)
#     # sys.exit()
#     # vector_db_file_path = os.path.join(tempfile.gettempdir(), "vector_store_new1.db")
#     vector_db_file_path='vector_store_new2'
#     # Delete the existing vector store file
#     # if os.path.exists(vector_db_file_path):
#         # os.remove(vector_db_file_path)
#     vector_store = create_or_load_vector_store(docs,vector_db_file_path)
#     print('done')
#     # vector_db_file_path='vector_store_new1'
#     # vector_store = initialize_vector_store(vector_db_file_path)
#     # query =  "tell me somting about the kabini"
#     # chain = get_chain(vector_db_file_path)
#     # result = chain.invoke(query)
#     # print(f"Query: {query}")
#     # print(f"Result: {result}\n")
