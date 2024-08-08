# import os
# import logging
# from typing import Dict, List, Any, Tuple
# from langchain.prompts import PromptTemplate, ChatPromptTemplate
# from langchain.chains import LLMChain, SequentialChain
# from langchain_community.vectorstores import FAISS
# from langchain_openai import ChatOpenAI
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain.memory import ConversationBufferWindowMemory
# from langchain.callbacks import get_openai_callback

# # Initialize embeddings and vector store
# embedding_model = "all-MiniLM-L6-v2"
# instruct_embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
# vector_db_file_path = 'vector_store_new_5'
# vector_db = FAISS.load_local(vector_db_file_path, instruct_embeddings, allow_dangerous_deserialization=True)
# retriever = vector_db.as_retriever(search_kwargs={"k": 5})
# llm = ChatOpenAI(model='gpt-4o-mini' ,api_key=os.environ['OPENAI_API_KEY'], temperature=0.5)

# # Initialize conversation memory with a window of last 5 interactions
# memory = ConversationBufferWindowMemory(k=5, memory_key="chat_history", input_key="query")
# # Booking state management
# booking_states = ['initial', 'destination', 'date', 'guests', 'login', 'payment']
# current_booking_state = 'initial'

# # Define your prompts
# context_analyzer_template = """Analyze the following query and chat history to determine the current context and any context switches.

# Query: {query}
# Chat History: {chat_history}
# Current Booking State: {booking_state}
# Default Destinations: {default_destinations}

# Provide a brief summary of the current context and explicitly state if there's a topic switch.
# Format your response as follows:
# Current Context: [Brief description of the current topic]
# Topic Switch: [Yes/No]
# Previous Topic: [Only if there's a topic switch, otherwise 'N/A']
# New Topic: [Only if there's a topic switch, otherwise 'N/A']
# Suggested Booking State: [Suggest the next booking state if applicable, otherwise 'N/A']
# Selected Destination: [Destination mentioned in query, or first default if none mentioned]

# Analysis:"""

# context_analyzer_prompt = PromptTemplate(
#     input_variables=["query", "chat_history", "booking_state","default_destinations"],
#     template=context_analyzer_template
# )

# classifier_template = """Given the following user query, context analysis, and booking state, classify the query into one of these categories: general, destination, activity, or booking.

# Context Analysis: {context_analysis}
# Query: {query}
# Current Booking State: {booking_state}

# Classification:"""

# classifier_prompt = PromptTemplate(
#     input_variables=["context_analysis", "query", "booking_state"],
#     template=classifier_template
# )

# response_template = """You are a helpful travel assistant managing a booking flow. Based on the following classification, context analysis, query, relevant information, and current booking state, generate an appropriate response. Be sure to address any context switches or topic changes noted in the context analysis.

# Classification: {classification}
# Context Analysis: {context_analysis}
# Query: {query}
# Relevant Information: {relevant_info}
# Current Booking State: {booking_state}
# Default Destinations: {default_destinations}

# Provide a concise and relevant response based on the current booking state and user query. Follow these guidelines:
# 1. If in 'initial' state, ask for the destination if not provided.
# 2. If in 'destination' state, confirm the destination and ask for the date.
# 3. If in 'date' state, confirm the date and ask for the number of guests (adults and children).
# 4. If in 'guests' state, confirm guest numbers and prompt for login for discount prices.
# 5. If in 'login' state, confirm login and provide a link to payment.
# 6. If in 'payment' state, guide the user to complete the payment process.

# Keep responses brief and relevant. If the user asks questions unrelated to the current booking state, answer them concisely and guide them back to the booking flow if appropriate.

# AI Assistant:"""

# response_prompt = PromptTemplate(
#     input_variables=["classification", "context_analysis", "query", "relevant_info", "booking_state","default_destinations"],
#     template=response_template
# )

# # Create LLMChains
# context_analyzer_chain = LLMChain(llm=llm, prompt=context_analyzer_prompt, output_key="context_analysis")
# classifier_chain = LLMChain(llm=llm, prompt=classifier_prompt, output_key="classification")
# response_chain = LLMChain(llm=llm, prompt=response_prompt, output_key="response")

# # Create SequentialChain
# sequential_chain = SequentialChain(
#     chains=[context_analyzer_chain, classifier_chain, response_chain],
#     input_variables=["query", "chat_history", "relevant_info", "booking_state","default_destinations"],
#     output_variables=["context_analysis", "classification", "response"],
#     verbose=True
# )


# def generate_response(query, chat_history ,relevant_info ,default_destinations):
#     global current_booking_state
#     try:
#         with get_openai_callback() as cb:
#             response = sequential_chain({
#                 "query": query,
#                 "chat_history": chat_history ,
#                 "relevant_info": relevant_info ,
#                 "booking_state": current_booking_state,
#                 "default_destinations": default_destinations
#                 })
        
#         print(f"\nContext Analysis:\n {response['context_analysis']}")
#         print(f"\nClassification: {response['classification']}")
#         print(f"Total Tokens: {cb.total_tokens}")
#         print(f"Prompt Tokens: {cb.prompt_tokens}")
#         print(f"Completion Tokens: {cb.completion_tokens}")
#         print(f"Total Cost (USD): ${cb.total_cost}")
#         print('\n')
#         print(f"query: ${query}")
#         print(f"chat_history: ${chat_history}")
#         print(f"relevant_info: ${relevant_info}")
#         print(f"\ncurrent_booking_state: ${current_booking_state}")
        
#         print('\n')
#         current_booking_state = update_booking_state(response['context_analysis'], current_booking_state)
#         print(f"\ncurrent_booking_state: ${current_booking_state}")

#         return  response['response'], response['context_analysis']
#     except Exception as e:
#         logging.error(f"Error in generate_response: {e}")
#         return "An error occurred while generating the response."

# def generate_query_response(query ):
#     print("\nReceived Query:", query)
#     try:
#         chat_history = memory.load_memory_variables({})["chat_history"]
#         # First, get the context analysis
#         print("\nchat_history\n",chat_history)

#         default_destinations = get_default_destination()
#         print('\nhii',default_destinations,'\nhii')
        
#         context_analysis = context_analyzer_chain.run(
#             query=query, 
#             chat_history=chat_history ,
#             booking_state=current_booking_state,
#             default_destinations=default_destinations
#             )
#         print("Context Analysis:", context_analysis)
        
#         relevant_info, documents = retrieve_and_filter_documents(query, context_analysis)
#         print('Retrieved and filtered documents')
#         print("relevant_info:", relevant_info)
        
#         response ,updated_context_analysis  = generate_response(query, chat_history ,relevant_info,default_destinations)
#         print("Generated Response:", response)
#         print("Generated updated_context_analysis:", updated_context_analysis)
        
        
#         # Update memory with the new interaction
#         memory.save_context({"query": query}, {"output": response})
        
#         seen_primary_keys = set()
#         document_metadata = []
        
#         for doc in documents:
#             primary_key = doc.metadata.get('eoexperience_primary_key')
#             name = doc.metadata.get('eoexperience_name')
#             if primary_key not in seen_primary_keys:
#                 document_metadata.append({
#                     'primary_key': primary_key,
#                     'name': name
#                 })
#                 seen_primary_keys.add(primary_key)
        
#         return {
#             'result': response,
#             'source_documents': documents,
#             'context': relevant_info,
#             'document_metadata': document_metadata ,
#             'context_analysis': updated_context_analysis,
#             'current_booking_state': current_booking_state
#         }
#     except Exception as e:
#         print(f"Error in generate_query_response: {e}")
#         import traceback
#         traceback.print_exc()
#         return {
#             'result': "An error occurred while processing your request.",
#             'source_documents': []
#         }

# def update_booking_state(context_analysis: str, current_state: str) -> str:
#     suggested_state = context_analysis.split("Suggested Booking State:")[-1].strip()
#     if suggested_state in booking_states:
#         return suggested_state
#     return current_state
# def get_default_destination() -> List[Tuple[str, str]]:
#     try:
#         # Query the vector store for documents
#         results = vector_db.similarity_search(
#             "",
#             k=500  # Retrieve more documents than needed to ensure we have enough after filtering
#         )

#         # Filter and process the results
#         filtered_destinations = {}
#         for doc in results:
            
#             primary_key = doc.metadata.get('eoexperience_primary_key')
#             display_priority = doc.metadata.get('display_priority')
#             eoexperience_name = doc.metadata.get('eoexperience_name', 'Unknown')
#             lkdestination_name = doc.metadata.get('lkdestination_name', 'Unknown')

#             # Only consider documents with display_priority < 3 and valid primary key
#             if (primary_key and display_priority     and display_priority < 2):
#                 # print('\n',doc,'\n')
#                 # If this primary key is not yet in our dictionary or has a lower display_priority
#                 if (primary_key not in filtered_destinations or
#                     display_priority < filtered_destinations[primary_key][1]):
#                     filtered_destinations[primary_key] = (eoexperience_name, lkdestination_name, display_priority)

#         # Sort the destinations by display_priority and take the top 10
#         sorted_destinations = sorted(filtered_destinations.values(), key=lambda x: x[2])[:10]

#         # Return the list of tuples (eoexperience_name, lkdestination_name)
#         return [(eo_name, lk_name) for eo_name, lk_name, _ in sorted_destinations]

#     except Exception as e:
#         logging.error(f"Error retrieving default destinations: {e}")
#         return []

# def retrieve_and_filter_documents(query, context_analysis):
#     try:
# # Check if there's a topic switch
#         if "Topic Switch: Yes" in context_analysis:
#             # If there's a topic switch, only use the query for retrieval
#             relevant_chunks = retriever.get_relevant_documents(query)
#         else:
#             # If no topic switch, use both query and context analysis for retrieval
#             combined_query = f"{query}\n\nContext: {context_analysis}"
#             relevant_chunks = retriever.get_relevant_documents(combined_query)

#         if relevant_chunks:
#             document_counts = {}
#             filtered_documents = []

#             for chunk in relevant_chunks:
#                 primary_key = chunk.metadata.get('eoexperience_primary_key')
#                 if primary_key not in document_counts:
#                     document_counts[primary_key] = 0

#                 if document_counts[primary_key] < 2:
#                     filtered_documents.append(chunk)
#                     document_counts[primary_key] += 1

#             sorted_documents = sorted(filtered_documents, key=lambda x: x.metadata.get('display_priority', float('inf')))
#             context = "\n".join([f"{doc.metadata.get('eoexperience_name')} {doc.metadata.get('lkdestination_name')}\n{doc.page_content}" for doc in sorted_documents])

#             return context, sorted_documents

#         return None, []
#     except Exception as e:
#         logging.error(f"Error retrieving and filtering documents: {e}")
#         raise

# # Example usage
# if __name__ == "__main__":
#     print("Starting the chatbot...")
    
#     while True:
#         user_query = input("You: ")
#         if user_query.lower() in ['quit', 'exit', 'bye']:
#             print("Assistant: Thank you for using our service. Have a great day!")
#             break
        
#         print("\nProcessing query:", user_query)
#         response = generate_query_response(user_query)
#         print("\nFull Response:", response)
#         print(f"Assistant: {response['result']}")