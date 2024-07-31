import os
import sys
import tempfile
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.nlp import get_chain
from app.utils.faiss_helper import create_or_load_vector_store, create_documents_from_db
load_dotenv()
if __name__ == "__main__":
    table_name = "eoexperience"  # Replace with your actual table name
    fields = ["primary_key", "name", "description", "location", "pin_code", "is_stay", "price", "latitude", "longitude", "display_priority"]
    # Create documents and vector store
    docs = create_documents_from_db(table_name, fields)
    vector_db_file_path = os.path.join(tempfile.gettempdir(), "vector_store_new1.db")

    # Delete the existing vector store file
    if os.path.exists(vector_db_file_path):
        os.remove(vector_db_file_path)

    vector_store = create_or_load_vector_store(docs, vector_db_file_path)

    # Example queries
    queries = [
        "What is the price for the scuba diving course in Pondicherry?",
        "What is the location of Red Earth, Kabini?",
        "Can I stay at a riverside resort in Dandeli?",
        "I want to do some activity in the water"
    ]

    for query in queries:
        chain = get_chain(vector_db_file_path)
        result = chain.invoke(query)
        print(f"Query: {query}")
        print(f"Result: {result}\n")
