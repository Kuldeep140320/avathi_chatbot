import os
import logging
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAI,ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

# Initialize embeddings and vector store
embedding_model = "all-MiniLM-L6-v2"
instruct_embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
vector_db_file_path = 'vector_store_new_5'
vector_db = FAISS.load_local(vector_db_file_path, instruct_embeddings, allow_dangerous_deserialization=True)
retriever = vector_db.as_retriever(search_kwargs={"k": 5})
llm = ChatOpenAI(model="gpt-4o-mini",api_key=os.environ['OPENAI_API_KEY'], temperature=0.6)

# Initialize ConversationBufferMemory
memory = ConversationBufferMemory()
# conversation = ConversationChain(
#     llm=llm, 
#     memory=memory,
#     verbose=True
# )
def embed_query(query):
    """Embed the query using the instructed embeddings model."""
    return instruct_embeddings.embed_query(query)
def retrieve_and_filter_documents(query):
    try:
        relevant_chunks = retriever.get_relevant_documents(query)
        if relevant_chunks:
            document_counts = {}
            filtered_documents = []

            for chunk in relevant_chunks:
                primary_key = chunk.metadata.get('eoexperience_primary_key')
                if primary_key not in document_counts:
                    document_counts[primary_key] = 0

                if document_counts[primary_key] < 2:
                    filtered_documents.append(chunk)
                    document_counts[primary_key] += 1

            sorted_documents = sorted(filtered_documents, key=lambda x: x.metadata.get('display_priority', float('inf')))
            # context = "\n".join([doc.page_content for doc in sorted_documents])
            context = "\n".join([f"{doc.metadata.get('eoexperience_name')} {doc.metadata.get('lkdestination_name')}\n{doc.page_content}" for doc in sorted_documents])

            return context, sorted_documents

        return None, []
    except Exception as e:
        logging.error(f"Error retrieving and filtering documents: {e}")
        raise

def generate_response(context, query):
    """Generate a response based on the provided context and query."""
    prompt_template = """You are a helpful assistant. Given the following context and a question, generate an answer based on this context only.
    If the answer is not directly found in the context, suggest relevant options based on the available information.
    If the context mentions activities or locations related to the query, include them in your suggestions.
    If no relevant information is found, state "I don't have enough information to provide an answer.
    Here are some related options you might consider: [suggest some activities or locations based on the context]."

    CONTEXT: {context}

    QUESTION: {question}"""

    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    response = llm.predict(PROMPT.format(context=context, question=query))
    return response
def genrate_query_response(query):
    """Handle the user query by retrieving and filtering documents, and then generating a response."""
    # query_embedding  = embed_query(query)
    context, documents = retrieve_and_filter_documents(query )
    if context:
        response = generate_response(context, query)
        seen_primary_keys = set()
        document_metadata = []
        
        for doc in documents:
            primary_key = doc.metadata.get('eoexperience_primary_key')
            name = doc.metadata.get('eoexperience_name')
            if primary_key not in seen_primary_keys:
                document_metadata.append({
                    'primary_key': primary_key,
                    'name': name
                })
                seen_primary_keys.add(primary_key)
        return {
            'result': response,
            'source_documents': documents,
            'context': context,
            'document_metadata': document_metadata 
        }
    return {
        'result': "No relevant information found.",
        'source_documents': []
    }

