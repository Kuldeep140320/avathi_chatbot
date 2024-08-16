from langchain.chains import LLMChain, SequentialChain
from app.models.llm import llm
from app.prompts.templates import context_analyzer_prompt, classifier_prompt, response_prompt,ui_analyzer_prompt ,parser,first_prompt_template,options_prompt_template
from langchain.output_parsers import PydanticOutputParser
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

context_analyzer_chain = LLMChain(llm=llm, prompt=context_analyzer_prompt, output_key="context_analysis")
classifier_chain = LLMChain(llm=llm, prompt=classifier_prompt, output_key="classification")
response_chain = LLMChain(llm=llm, prompt=response_prompt, output_key="response")
first_prompt_chain = LLMChain(llm=llm, prompt=first_prompt_template)
option_prompt_chain = LLMChain(llm=llm, prompt=options_prompt_template)

 
ui_analyzer_chain = LLMChain(
    llm=llm, 
    prompt=ui_analyzer_prompt, 
    output_key="ui_analysis",
    output_parser=parser
)

sequential_chain = SequentialChain(
    chains=[context_analyzer_chain, classifier_chain, response_chain],
    input_variables=["query", "chat_history", "relevant_info", "booking_state"],
    output_variables=["context_analysis", "classification", "response"],
    verbose=True
)