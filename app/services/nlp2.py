import os
import logging
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.memory import ConversationBufferMemory

# Initialize embeddings and vector store
embedding_model = "all-MiniLM-L6-v2"
instruct_embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
vector_db_file_path = 'vector_store_new2'
vector_db = FAISS.load_local(vector_db_file_path, instruct_embeddings, allow_dangerous_deserialization=True)
retriever = vector_db.as_retriever(search_kwargs={"k": 5})
llm = OpenAI(api_key=os.environ['OPENAI_API_KEY'], temperature=0.6)

# Initialize ConversationBufferMemory
memory = ConversationBufferMemory()

def retrieve_and_filter_documents(query):
    try:
        relevant_chunks = retriever.get_relevant_documents(query)
        if relevant_chunks:
            unique_documents = {}
            for chunk in relevant_chunks:
                primary_key = chunk.metadata.get('primary_key')
                if primary_key not in unique_documents:
                    unique_documents[primary_key] = chunk
            sorted_documents = sorted(unique_documents.values(), key=lambda x: x.metadata.get('display_priority', float('inf')))
            context = "\n".join([doc.page_content for doc in sorted_documents])
            return context, sorted_documents
        return None, []
    except Exception as e:
        logging.error(f"Error retrieving and filtering documents: {e}")
        raise
def generate_response(context, query):
    """Generate a response based on the provided context and query."""
    prompt_template = """Given the following context and a question, generate an answer based on this context only.
    If the answer is not directly found in the context, try to infer a relevant answer based on the available information.
    If no relevant information is found, kindly state "I don't have enough information to provide an answer."

    CONTEXT: {context}

    QUESTION: {question}"""

    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    response = llm.predict(PROMPT.format(context=context, question=query))
    return response
def handle_query(query):
    """Handle the user query by retrieving and filtering documents, and then generating a response."""
    context, documents = retrieve_and_filter_documents(query)
    if context:
        response = generate_response(context, query)
        return {
            'result': response,
            'source_documents': documents
        }
    return {
        'result': "No relevant information found.",
        'source_documents': []
    }

