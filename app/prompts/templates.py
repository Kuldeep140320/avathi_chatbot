from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List

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


# class Experience(BaseModel):
#     id: str = Field(description="ID of the experience")
#     name: str = Field(description="Name of the experience")

class UIAnalysis(BaseModel):
    date_picker: bool = Field(description="Whether to show the date picker")
    options_list: bool = Field(description="Whether to show the options list")
    login_popup: bool = Field(description="Whether to show the login popup")
    payment_link: bool = Field(description="Whether to show the payment link")
    guest_info_form: bool = Field(description="Whether to show the guest info form")
    # experiences: List[Experience] = Field(description="List of relevant experiences short according to user query", default=[])


parser = PydanticOutputParser(pydantic_object=UIAnalysis)

ui_analyzer_template = """
Analyze the following response, context analysis, booking state  to determine what UI elements should be shown to the user at one time only one UI elements will be true.

Response: {response}
Context Analysis: {context_analysis}
Current Booking State: {booking_state}

Based on this information, determine:
1. Should a date picker be shown? (Only if dates haven't been selected)
2. Should a login popup be shown? (Only if user isn't logged in and it's appropriate)
3. Should a payment link be shown? (Only if booking is ready for payment and not already paid)
4. Should a guest information form be shown? (Only if guest info hasn't been provided)
5. Should an options list for relevant experiences be shown? (Only if not already selected)

Do not provide reasons for your decisions. Only return true or false for each UI element.

{format_instructions}

Analysis:
"""

ui_analyzer_prompt = PromptTemplate(
    input_variables=["response", "context_analysis", "booking_state"],
    template=ui_analyzer_template,
    partial_variables={"format_instructions": parser.get_format_instructions()}
) 


first_prompt_template = PromptTemplate(
    input_variables=["query"],
    template="""You are a helpful travel booking assistant. Your task is to understand the user's initial query and respond appropriately.

User Query: {query}

If the user is asking about travel or destinations, respond enthusiastically and ask where they want to go.
If the user's query is not related to travel or is unclear, politely state that you don't understand and ask if they have any travel-related questions.

Please structure your response as follows:
1. A brief greeting
2. Your understanding of their query or a request for clarification
3. A question to guide the conversation towards travel planning

Response:"""
)

# first_prompt_chain = LLMChain(llm=llm, prompt=first_prompt_template)

options_prompt_template = PromptTemplate(
                input_variables=["query", "options"],
                template="""
                User Query: {query}
                Available Options: {options}

                Generate a friendly and helpful response to the user's query. If there are relevant options, mention that we have several options without listing them all, and encourage the user to select from the dropdown or provide more details about their preferences. If the query is about a specific activity or booking, tailor the response accordingly. Keep the response concise and engaging.

                Response:
                """
            )