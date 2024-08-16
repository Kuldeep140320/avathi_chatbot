import os
import sys
# import tempfile
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from app.services.nlp import get_chain
from app.utils.faiss_helper import create_or_load_vector_store, create_documents_from_db
# from app.utils.faiss_helper import initialize_vector_store

load_dotenv()
if __name__ == "__main__":
    table_name = "eoexperience"  # Replace with your actual table name
    fields = ["primary_key", "name", "description", "location", "address", "price" ,"display_priority"]
    # Create documents and vector store
    docs = create_documents_from_db(table_name, fields)
    # print(docs)
    # sys.exit()
    # vector_db_file_path = os.path.join(tempfile.gettempdir(), "vector_store_new1.db")
    vector_db_file_path='vector_store_new_9'
    # Delete the existing vector store file
    # if os.path.exists(vector_db_file_path):
        # os.remove(vector_db_file_path)
    vector_store = create_or_load_vector_store(docs,vector_db_file_path)
    print('done')
    # vector_db_file_path='vector_store_new1'
    # vector_store = initialize_vector_store(vector_db_file_path)
    # query =  "tell me somting about the kabini"
    # chain = get_chain(vector_db_file_path)
    # result = chain.invoke(query)
    # print(f"Query: {query}")
    # print(f"Result: {result}\n")
