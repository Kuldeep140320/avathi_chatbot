import os
import json
import faiss
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import OpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
import sys


# Load Faiss index and metadata
index = faiss.read_index('bookingChainExpTicket-all-MiniLM-L6-v2.index')
with open('bookingChainExpTicket-all-MiniLM-L6-v2_metadata.json', 'r') as f:
    metadata = json.load(f)
print('hii')
sys.exit()
embedding_model = "all-MiniLM-L6-v2"
instruct_embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

# Create a retriever using the loaded index and metadata
vector_db = FAISS(index, instruct_embeddings)
retriever = vector_db.as_retriever(search_kwargs={"k": 5})

llm = OpenAI(api_key=os.environ['OPENAI_API_KEY'], temperature=0.6)

# Initialize ConversationChain
conversation = ConversationChain(
    llm=llm,
    memory=ConversationBufferMemory()
)

def extract_info_from_query(query):
    relevant_chunks = retriever.get_relevant_documents(query)
    print(relevant_chunks)
    if relevant_chunks:
        metadata = relevant_chunks[0].metadata
        experience_id = metadata.get('exp_id')
    else:
        experience_id = None

    date_prompt = f"Extract and format the start and end dates from this query in YYYY-MM-DD format if dates are present: {query}. If no dates are present, return 'No dates found'."
    date_response = llm.predict(date_prompt)
    print('date_response')
    print(date_response)
    start_date, end_date = parse_date_response(date_response)
    return experience_id, start_date, end_date

def parse_date_response(response):
    # Implement logic to parse the LLM response and extract formatted dates
    lines = response.split('\n')
    start_date = end_date = None
    for line in lines:
        if 'start date:' in line.lower():
            start_date = line.split(':')[1].strip()
        elif 'end date:' in line.lower():
            end_date = line.split(':')[1].strip()
    return start_date, end_date

def getQueryResponse(user_query, selected_exp_id=None):
    arr_res = []
    print("user_query, selected_exp_id")
    print(user_query, selected_exp_id)
    experience_id, start_date, end_date = extract_info_from_query(user_query)
    if selected_exp_id:
        experience_id = selected_exp_id

    if experience_id and start_date and end_date:
        price_data = get_price_by_date(experience_id, start_date, end_date)
        llm_prompt = f"""
                Experience ID: {experience_id}
                Start date: {start_date}
                End date: {end_date}
                Price data: {price_data}

                Generate a response summarizing the booking details and pricing information.
                """
        response = llm.predict(llm_prompt)
        arr_res = [response, price_data]
        return arr_res

    # Search for relevant experiences
    relevant_chunks = retriever.get_relevant_documents(user_query)

    if relevant_chunks:
        experiences = []
        for chunk in relevant_chunks:
            metadata = chunk.metadata
            exp_id = metadata.get('exp_id')
            location = metadata.get('location')
            name = metadata.get('name')
            if exp_id and name:
                experiences.append({"id": exp_id, "name": name,"location":location})

        if experiences:
            llm_prompt = f"""
                       User query: {user_query}
                       Available experiences: {experiences}

                       Generate a response suggesting the available experiences based on the user's query. 
                       If the query mentions a specific location, prioritize experiences in that location.
                       """
            response = llm.predict(llm_prompt)
            arr_res.append(response)
            arr_res.append({"experiences": experiences})
            return arr_res

    # If no experiences found or if it's a follow-up query
    response = conversation.predict(input=user_query)
    arr_res = [response]

    return arr_res

def get_recommendations(user_query):
    return getQueryResponse(user_query)
