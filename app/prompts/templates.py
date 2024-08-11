from langchain.prompts import PromptTemplate

context_analyzer_template = """Analyze the following query and chat history to determine the current context and any context switches.

Query: {query}
Chat History: {chat_history}
Current Booking State: {booking_state}

Provide a brief summary of the current context and explicitly state if there's a topic switch.
Format your response as follows:
Current Context: [Brief description of the current topic]
Topic Switch: [Yes/No]
Previous Topic: [Only if there's a topic switch, otherwise 'N/A']
New Topic: [Only if there's a topic switch, otherwise 'N/A']
Suggested Booking State: [Suggest the next booking state:  'initial','destination', 'date', 'guests', 'login', or 'payment']
Selected Destination: [Destination mentioned in query, or first default if none mentioned]

Analysis:"""

context_analyzer_prompt = PromptTemplate(
    input_variables=["query", "chat_history", "booking_state","default_destinations"],
    template=context_analyzer_template
)

classifier_template = """Given the following user query, context analysis, and booking state, classify the query into one of these categories: general, destination, activity, or booking.

Context Analysis: {context_analysis}
Query: {query}
Current Booking State: {booking_state}

Classification:"""

classifier_prompt = PromptTemplate(
    input_variables=["context_analysis", "query", "booking_state"],
    template=classifier_template
)

response_template = """You are a helpful travel assistant managing a booking flow. Based on the following classification, context analysis, query, relevant information, and current booking state, generate an appropriate response. Be sure to address any context switches or topic changes noted in the context analysis.

Classification: {classification}
Context Analysis: {context_analysis}
Query: {query}
Relevant Information: {relevant_info}
Current Booking State: {booking_state}

Provide a concise and relevant response based on the current booking state and user query. Follow these guidelines:
1. If in 'initial' state, ask for the destination if not provided.
2. If in 'destination' state, confirm the destination and ask for the date.
3. If in 'date' state, confirm the date and ask for the number of guests (adults and children).
4. If in 'guests' state, confirm guest numbers and prompt for login for discount prices.
5. If in 'login' state, confirm login and provide a link to payment.
6. If in 'payment' state, guide the user to complete the payment process.

Keep responses brief and relevant. If the user asks questions unrelated to the current booking state, answer them concisely and guide them back to the booking flow if appropriate.

AI Assistant:"""

response_prompt = PromptTemplate(
    input_variables=["classification", "context_analysis", "query", "relevant_info", "booking_state","default_destinations"],
    template=response_template
)
