from langchain.chains import LLMChain, SequentialChain
from app.models.llm import llm
from app.prompts.templates import context_analyzer_prompt, classifier_prompt, response_prompt

context_analyzer_chain = LLMChain(llm=llm, prompt=context_analyzer_prompt, output_key="context_analysis")
classifier_chain = LLMChain(llm=llm, prompt=classifier_prompt, output_key="classification")
response_chain = LLMChain(llm=llm, prompt=response_prompt, output_key="response")

sequential_chain = SequentialChain(
    chains=[context_analyzer_chain, classifier_chain, response_chain],
    input_variables=["query", "chat_history", "relevant_info", "booking_state"],
    output_variables=["context_analysis", "classification", "response"],
    verbose=True
)