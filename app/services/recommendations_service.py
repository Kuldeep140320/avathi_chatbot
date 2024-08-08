# import os
# from dotenv import load_dotenv
# from langchain.prompts import PromptTemplate
# from langchain.chains import RetrievalQA
# from bs4 import BeautifulSoup
# import pandas as pd
# from langchain.docstore.document import Document
# from typing import List
# from langchain_community.vectorstores import FAISS
# from langchain_openai import OpenAI
# from langchain_huggingface import HuggingFaceEmbeddings
# import tempfile
# import psycopg2
# import  sys
# temp_dir = tempfile.mkdtemp()

# # Load environment variables
# load_dotenv()

# # Initialize the LLM and embeddings
# llm = OpenAI(api_key=os.environ['OPENAI_API_KEY'], temperature=0.6)
# embedding_model = "all-MiniLM-L6-v2"
# instruct_embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
# vector_db_file_path = os.path.join(temp_dir, "vector_store_new.db")

# def clean_html(raw_html):
#     """Clean HTML tags from a string."""
#     cleantext = BeautifulSoup(raw_html, "lxml").text
#     return cleantext

# def fetch_data_from_table(table_name: str, fields: List[str]) -> pd.DataFrame:
#     """Fetch data from the specified table in the database."""
#     conn = get_db_connection()
#     query = f'SELECT {", ".join(fields)} FROM "{table_name}" WHERE is_active = TRUE and display_priority < 5'
#     df = pd.read_sql(query, conn)
#     conn.close()
#     return df

# def get_db_connection():
#     """Get the database connection."""
#     return psycopg2.connect(
#         host=os.getenv("DB_HOST"),
#         port=os.getenv("DB_PORT"),
#         dbname=os.getenv("DB_NAME"),
#         user=os.getenv("DB_USER"),
#         password=os.getenv("DB_PASSWORD")
#     )

# def create_documents_from_db(table_name: str, fields: List[str]) -> List[Document]:
#     """Create documents from database records with vector embeddings."""
#     df = fetch_data_from_table(table_name, fields)
#     # print(df)
#     # sys.exit()
#     documents = []
#     for _, row in df.iterrows():
#         content = f"Name: {row['name']}\n"
#         content += f"Description: {clean_html(row['description'])}\n"
#         content += f"Location: {row['location']}\n"
#         content += f"Pin Code: {row['pin_code']}\n"
#         content += f"Is Stay: {'Yes' if row['is_stay'] else 'No'}\n"
#         content += f"Price: {row['price']}\n"
#         content += f"Latitude: {row['latitude']}\n"
#         content += f"Longitude: {row['longitude']}\n"

#         # Generate vector embedding for the content
#         embedding = instruct_embeddings.embed_query(content)

#         doc = Document(
#             page_content=content,
#             metadata={
#                 "primary_key": row['primary_key'],
#                 "name": row['name'],
#                 "location": row['location'],
#                 "is_stay": row['is_stay'],
#                 "price": row['price'],
#                 "latitude": row['latitude'],
#                 "longitude": row['longitude'],
#                 "display_priority": row['display_priority']
#             },
#             embedding=embedding  # Store the embedding with the document
#         )
#         documents.append(doc)
#     return documents

# def create_or_load_vector_store(docs: List[Document], store_path: str):
#     """Create or load a vector store with embeddings."""
#     if (os.path.exists(store_path)):
#         vector_store = FAISS.load_local(store_path, instruct_embeddings, allow_dangerous_deserialization=True)
#         print("Loaded existing vector store.")
#     else:
#         vector_store = FAISS.from_documents(docs, instruct_embeddings)
#         vector_store.save_local(store_path)
#         print("Created and saved new vector store.")
#     return vector_store

# def get_chain():
#     """Create the RetrievalQA chain."""
#     vector_db = FAISS.load_local(vector_db_file_path, embeddings=instruct_embeddings, allow_dangerous_deserialization=True)
#     retriever = vector_db.as_retriever(search_kwargs={"k": 5})
#     print("get_chain")
#     prompt_template = """Given the following context and a question, generate an answer based on this context only.
#     If the answer is not directly found in the context, try to infer a relevant answer based on the available information.
#     If no relevant information is found, kindly state "I don't have enough information to provide an answer."

#     CONTEXT: {context}

#     QUESTION: {question}"""
#     PROMPT = PromptTemplate(
#         template=prompt_template, input_variables=["context", "question"]
#     )

#     chain = RetrievalQA.from_chain_type(
#         llm=llm,
#         chain_type="stuff",
#         retriever=retriever,
#         input_key="query",
#         return_source_documents=True,
#         chain_type_kwargs={"prompt": PROMPT}
#     )
#     return chain

# def streamlit_query(query):
#     """Handle a query in a Streamlit app."""
#     chain = get_chain()
#     response = chain({"query": query})
#     result = response['result']
#     return result

# if __name__ == "__main__":
#     table_name = "eoexperience"  # Replace with your actual table name
#     fields = ["primary_key","name", "description", "location", "pin_code", "is_stay", "price", "latitude", "longitude","display_priority"]

#     # Create documents and vector store
#     docs = create_documents_from_db(table_name, fields)

#     # Delete the existing vector store file
#     if os.path.exists(vector_db_file_path):
#         os.remove(vector_db_file_path)

#     vector_store = create_or_load_vector_store(docs, vector_db_file_path)

#     # Example queries
#     queries = [
#         "What is the price for the scuba diving course in Pondicherry?",
#         "What is the location of Red Earth, Kabini?",
#         "Can I stay at a riverside resort in Dandeli?",
#         "I want to do some activity in the water"
#     ]

#     for query in queries:
#         chain = get_chain()
#         result = chain.invoke(query)
#         print(f"Query: {query}")
#         print(f"Result: {result}\n")
