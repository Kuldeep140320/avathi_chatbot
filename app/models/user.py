# from langchain.chat_models import ChatOpenAI
# import openai
# from langchain.memory import ChatMessageHistory
# from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
# from kaitongo.settings import OPENAPI_TOKEN
# import pandas as pd
# from kaitongo.helpers import level0_weaviate_connector
 
# model = "gpt-4o"
 
# def convert_chat_history_to_messages(chat_history):
#     messages = []
#     for message in chat_history.messages:
#         if isinstance(message, HumanMessage):
#             messages.append({"role":"user","content": message.content})
#         elif isinstance(message, AIMessage):
#             messages.append({"role":"assistant","content": message.content})
#         elif isinstance(message, SystemMessage):
#             messages.append({"role":"system","content": message.content})
#     return messages
 
# class UserRequest:
#     def __init__(self, _chat_history, _llm, _company, _report_type, _is_ready, _context, _companies_list):
#         self.chat_history = _chat_history
#         self.llm = _llm
#         self.is_ready = _is_ready
#         self.company = _company
#         self.report = _report_type
#         self.companies_list = _companies_list
#         self.context = _context
#         self.use_ai = False
 
#     def query_and_save(self, user_input):
 
#         self.chat_history.add_user_message(HumanMessage(content=user_input))      
 
#         ai_response = self.llm.chat.completions.create(
#             model= model,
#             messages= convert_chat_history_to_messages(self.chat_history),
#             tools= functions,
#         )
 
#         if ai_response.choices[0].message.content != None:
#             next_ai_message(self)
 
#         elif ai_response.choices[0].message.tool_calls != None:
#             self.chat_history.add_ai_message(str(ai_response.choices[0].message.tool_calls))
 
#             for tool in ai_response.choices[0].message.tool_calls:
#                 args = tool.function.arguments
#                 func = tool.function.name
 
#                 if func == "set_report":
#                     set_report(args, self)
                    
#                 elif func == "set_company":
#                     set_company(args, self)
 
#                 elif func == "set_context":
#                     set_context(args, self)
 
#                 elif func == "set_report_ready":
#                     set_report_ready(args, self)
 
#                 elif func == "set_new":
#                     set_new(self)
            
#             if func != "set_new":
#                 next_ai_message(self)
 
#     def get_chat_history(self):
#         return self.chat_history
    
#     def get_most_recent_message(self):
#         return self.chat_history.messages[-1].content
    
#     def get_companies_list(self):
#         return self.companies_list
 
#     def get_user_request(self):
#         return {"report_ready": self.is_ready, "report_type": self.report, "company": self.company, "context":self.context}
    
 
    
# def initiate_chat():
#     chat_history = ChatMessageHistory()
#     llm = openai.OpenAI(api_key = OPENAPI_TOKEN)
                
#     system_message=  """ You are an AI chatbot. Your only tasks are to get information from the user and to help them make decisions. You do not generate any reports.
#     This is the information you need to get from the user. Call the appropriate functions when the user gives you information:
#     - Company Name: The name of the company they want a report about.
#     - Report Type: The style/format of the report. There are two options: quick or detailed. If the user doesn't know which they want, you must help them choose based on the following descriptions:
#       Quick report: A brief snapshot of the company, highlighting key developments. Ideal for early stage targeting and prospecting.
#       Detailed report: A comprehensive analysis of the company and it's sector. Suitable for key accounts and companies the user is already familiar with.
#     - Context: Pass either the context or "NA" as argument
#     - Is ready: When the user has given all the information they want to give and is ready for you to generate the report. True if the report is ready to generate.
 
#     These are the functions you can call:
#     - set_company: When the user tells you a company name. send company name as an argument.
#     - set_report: When you are sure which report type the user wants, either detailed or quick. If you are suggesting the report type/style to user, be sure to verify with them before calling this function. Send report type as an argument.
#     - set_context: When the user answers the question "is there any context you would like to include?". Pass either the user's context as an argument for context, or "NA" as the argument.
#     - set_report_ready: When the user is ready for the report. Send is ready True or False as an argument. DO NOT generate report, that is NOT your job.
#     - set_new: You can call this when the user is ready to start a different report.
    
#     Remember: Do not generate a report. Your only tasks are to get information from the user and to help them make decisions.
#     """
#     chat_history.add_message(SystemMessage(content=system_message))
 
#     system_message = f"If they aren't ready to generate another report then you can politely wait until they are ready. Call set_company() if they tell you a company name, call set_report() if they tell you a report type, and call set_context() if they have context to add."
#     chat_history.add_message(SystemMessage(content=f"Instructions for what to do when the user replies:{system_message}."))
 
#     ai_message = "What company would you like a report for?"
#     chat_history.add_ai_message(ai_message)
 
#     return chat_history, llm
 
 
# def create_chat_history_from_input(input):
#     chat_history = ChatMessageHistory()
    
#     for message in input:
#         for role, content in message.items():
#             #print( role, content )
#             if role == "AI":
#                 chat_history.add_ai_message(content)
#             elif role == "Human":
#                 chat_history.add_user_message(HumanMessage(content=content))
    
#     return chat_history
 
 
# def convert_chat_history_to_list(chat_history):
#     messages_list = []
#     for message in chat_history.messages:
#         if isinstance(message, HumanMessage):
#             messages_list.append({"Human": message.content})
#         elif isinstance(message, AIMessage):
#             messages_list.append({"AI": message.content})
#         elif isinstance(message, SystemMessage):
#             messages_list.append({"System": message.content})
 
#     return messages_list
 
 
# def run_insights_assistant(user_input=None, chat_history=None, company=None, report_type=None, report_ready=False, companies_list=None, context=None):
#     if not chat_history:
#         chat_history, llm = initiate_chat()
#         chatbot = UserRequest(chat_history, llm, company, report_type, report_ready, context, companies_list)
#         return  chatbot.get_most_recent_message(), convert_chat_history_to_list(chat_history), chatbot.get_user_request(), chatbot.get_companies_list()
    
#     else:
#         llm = openai.OpenAI(api_key = OPENAPI_TOKEN)
#         chat_history = create_chat_history_from_input(chat_history)
#         chatbot = UserRequest(chat_history, llm, company, report_type, report_ready, context, companies_list)
#         chat_history_list = convert_chat_history_to_list(chat_history)
 
#         if {'AI': 'What company would you like a report for?'} in chat_history_list or {'AI': "Ok, what company would you like to generate a new report for?"} in chat_history_list:
#             if company == None and companies_list == None:
#                 chatbot.use_ai = True
#             if company == None and companies_list != None:
#                 chatbot.use_ai = True # need to trigger AI now
#             if company != None:
#                 chatbot.use_ai = False # need to turn off AI now
#         if {'AI': "Would you like a detailed report or a quick report? If you aren't sure I can explain the difference and help you decide."} in chat_history_list:
#             if report_type == None:
#                 chatbot.use_ai = True
#             elif report_type != None:
#                 chatbot.use_ai = False
#         if {'AI': "Would you like to add any context before generating the report?"} in chat_history_list:
#             if context == None:
#                 chatbot.use_ai = True   
#             elif context != None:
#                 chatbot.use_ai = False
#         if {'AI': "Are you ready to generate the report?"} in chat_history_list:
#             if report_ready == False:
#                 chatbot.use_ai = True
#             elif report_ready == True:
#                 chatbot.use_ai = False
#         if chat_history_list.count({'AI': "I'm sorry, I've gotten confused. Can you repeat that?"}) > 3:
#             chatbot.chat_history.add_message(SystemMessage(content = f"Take the user's email address and end the chat."))
#             ai_message = "Please share your email address and someone will be in contact to help."
#             if chat_history_list.count("Please share your email address and someone will be in contact to help.")>=1:
#                 chatbot.chat_history.add_message(SystemMessage(content=f"If the user wants a new report, call the function set_new()."))
#                 ai_message = "Thanks, let me know if you would like to start a new report."
#             chatbot.chat_history.add_ai_message(ai_message)
#             chatbot.use_ai = False
#         chatbot.query_and_save(user_input)  
 
#         return chatbot.get_most_recent_message(),  convert_chat_history_to_list(chat_history), chatbot.get_user_request(), chatbot.get_companies_list()
    
   
# # finds best match to user input
# def search(class_name, weaviate_client, company, limit=3):
#     content = (
#         weaviate_client.query
#         .get(class_name, ["company", "ticker"])
#         .with_hybrid(query = company)
#         .with_additional(["score"])       
#         .with_limit(limit)        
#         .do()
#     )
#     results = []
#     for result in content['data']['Get'][class_name]:
#         results.append(result['company'])
#     return results
 
 
# def next_ai_message(chatbot):
#     # Help prepare chat for the next response
#     #print("\n--Chat history: ", convert_chat_history_to_list(chatbot.chat_history), "--\n")
#     if chatbot.report != None and chatbot.company != None and chatbot.is_ready == False and chatbot.context == None:
#         system_message = f"""Ask the user to provide context until they either want to see the report, have no more context to share, or want to make other changes.
#                             If they don't want to provide context then you can call set_report_ready() and it will generate the report for them.
#                             If they do want to share context then you should summarize all the context you know and pass it to set_context() as context argument. """
#         ai_message = f"Would you like to add any context before generating the report?"
 
#     elif chatbot.report != None and chatbot.company != None and chatbot.context != None and chatbot.is_ready == False:
#         system_message = "If the user wants to make changes you must adjust accordingly. Call set_company() if they tell you a new company name, call set_report() if they want to change the report type, and call set_context() if they have context to add. When the user is ready to see the report, you can call set_report_ready() with True as the is_Ready argument. This will show them the report. You are not allowed to generate a report."
#         ai_message = f"Are you ready to generate the report?"
    
#     elif chatbot.report != None and chatbot.company != None and chatbot.is_ready == True:
#         system_message = "The user has now read the report. If they don't have any changes, call the function set_new(). If they do have changes then call function set_report_ready() with False as the is_ready argument."
#         ai_message = f"Great, here's the report. Is there anything you would like to change?"
 
#     elif chatbot.company == None:
#         if chatbot.companies_list == None:
#             system_message = f"Figure out what company the user wants a report for and call set_company with the company as the argument. After you know, figure out the rest of the informtion."
#             ai_message = f"What company would you like a report for?"
#         elif chatbot.companies_list != None:
#             #system_message = f"The user say one of these companies or they may just say their respective number:  \n1.{chatbot.companies_list[0]} \n2.{chatbot.companies_list[1]} \n3.{chatbot.companies_list[2]}. Call the function set_company() with their choice as a the company argument. If they don't tell you, help them."
#             system_message = f"You said: \"I found some companies that match: \n1.{chatbot.companies_list[0]} \n2.{chatbot.companies_list[1]} \n3.{chatbot.companies_list[2]} \nWhich would you like a report for?\" to the user. They will tell you a company name from the list, or the number it is associated with. Call the function set_company() with their choice as a the company argument."
#             #ai_message = f"__I found some companies that match: \n1.{chatbot.companies_list[0]} \n2.{chatbot.companies_list[1]} \n3.{chatbot.companies_list[2]} \nWhich would you like a report for?__"
#             ai_message = "I found some companies that match:"
#             chatbot.use_ai = False
#     elif chatbot.report == None and chatbot.company != None:
#         system_message = "The user will either tell you that they want a detailed report or quick report, or they will ask for help. Help them decide if they need it. When you know: call set_report() with the report type (either detailed or quick) as the report_type argument. Tell the user: Quick report is a brief snapshot of the company, highlighting key developments. Ideal for early stage targeting and prospecting. Detailed report is a comprehensive analysis of the company and it's sector. Suitable for key accounts and companies the user is already familiar with."
#         ai_message = f"Would you like a detailed report or a quick report? If you aren't sure I can explain the difference and help you decide."   
 
#     else:
#         system_message = f"Here is what you know so far, ignore all Nones: report type: {chatbot.report}, company name: {chatbot.company}, list of possible companies: {chatbot.companies_list}, is report ready: {chatbot.is_ready}, context: {chatbot.context}. Figure out any missing information."
#         ai_message = "I'm sorry, I've gotten confused. Can you repeat that?"
 
#     if chatbot.use_ai:
#         chatbot.chat_history.add_message(SystemMessage(content=f"Tell this to the user in a way that makes sense with the conversation: Ask user: {ai_message}. Instructions for what to do after the user replies:{system_message}. IMPORTANT INSTRUCTION: The report is generated separately from this chat so you must not write a report for the user under any circumstance."))
#         ai_message2 = chatbot.llm.chat.completions.create(model= model, messages= convert_chat_history_to_messages(chatbot.chat_history)).choices[0].message.content
#         chatbot.chat_history.add_ai_message(ai_message2)
    
#     elif not chatbot.use_ai:
#         chatbot.chat_history.add_ai_message(ai_message)
 
 
# # function to be called to get the closest company names and next AI message
# def get_company_match(company, chatbot):
#     # find possible company options
#     chatbot.company = None
#     user_input = company[12:len(company)-2]
#     class_name = "Company_ticker"
#     weaviate_client = level0_weaviate_connector()
#     results = search(class_name, weaviate_client, user_input)
#     if user_input.strip() in results or user_input.strip(".") in results:
#         chatbot.company = user_input.strip()
#         chatbot.use_ai = False
#         return None
#     chatbot.companies_list = results
 
# # this function is called to set the report and next AI message
# def set_report(ai_response, chatbot):
#     # set report type
#     if "quick" in ai_response:
#         chatbot.report = "quick"
#         chatbot.use_ai = False
#     elif "detailed" in ai_response:
#         chatbot.report = "detailed"
#         chatbot.use_ai = False
 
# # this function is called to set the company and next AI message
# def set_company(company, chatbot):
#     # set company
#     chatbot.company = None
#     if chatbot.companies_list == None:
#         get_company_match(company, chatbot)
#     elif company[12:len(company)-2] not in chatbot.companies_list:
#         get_company_match(company, chatbot)
#     else:
#         chatbot.company = company[12:len(company)-2]
#         chatbot.use_ai = False
 
# # This function is called to end the conversation
# def set_report_ready(is_ready, chatbot):
#     if "True" in is_ready and chatbot.company != None and chatbot.report != None:
#         chatbot.is_ready = True
#         chatbot.use_ai = False
#     else:
#         chatbot.is_ready = False
#         system_message = f"Ask if user has any changes to the report"
#         chatbot.chat_history.add_message(SystemMessage(content=system_message))
 
# def set_context(context, chatbot):
#     chatbot.context = context
#     chatbot.use_ai = False
 
# def set_new(chatbot):
#     chatbot.report = None
#     chatbot.company = None
#     chatbot.is_ready = False
#     chatbot.context = None
#     chatbot.companies_list = None
#     chatbot.use_ai = False
#     chatbot.chat_history = ChatMessageHistory()
#     system_message= """ You are an AI chatbot helping the user provide information to generate a report. Your only tasks are to get information from the user and to help them make decisions.
#     This is the information you need to get from the user. Call the appropriate functions when the user gives you information.:
#     - Company Name: The name of the company they want a report about.
#     - Report Type: The style/format of the report. There are two options: quick or detailed. If the user doesn't know which they want, you must help them choose based on the following descriptions:
#       Quick report: A brief snapshot of the company, highlighting key developments. Ideal for early stage targeting and prospecting.
#       Detailed report: A comprehensive analysis of the company and it's sector. Suitable for key accounts and companies the user is already familiar with.
#     - Context: Pass either the context or "NA" as argument
#     - Is ready: When the user has given all the information they want to give and is ready for you to generate the report. True if the report is ready to generate.
 
#     These are the functions you can call:
#     - set_company: When the user tells you a company name. send comany name as an argument.
#     - set_report: When you are sure which report type the user wants, either detailed or quick. If you are suggesting the report type/style to user, be sure to verify with them before calling this function. Send report type as an argument.
#     - set_context: When the user answers the question "is there any context you would like to include?". Either the user context or "NA" as argument.
#     - set_report_ready: When the user is eady for the report. Send is ready True or False as an argument.
#     - set_new: You can call this when the user is ready to start a different report.
    
#     Remember: it is not your job to generate a report. Your job is only to get information from the user and to help them make decisions if they need help.
#     """
#     chatbot.chat_history.add_message(SystemMessage(content=system_message))
#     system_message = f"If they aren't ready to generate another report then you can politely wait until they are ready. Call set_company() if they tell you a company name, call set_report() if they tell you a report type, and call set_context() if they have context to add. If they don't give you any information, ask them what company they want to generate a report for."
#     chatbot.chat_history.add_message(SystemMessage(content=f"Instructions for what to do when the user replies:{system_message}."))
#     ai_message = "Ok, what company would you like to generate a new report for?"
#     chatbot.chat_history.add_ai_message(ai_message)
 
 
# # functions available to the GPT (defined above)
# functions = [
#     {
#     "type": "function",
#         "function": {
#         "name": "set_report",
#         "description": "When you are sure which report type/style the user wants, either detailed or quick.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "report_type": {
#                     "type": "string",
#                     "description": "The type/style of the report the user wants. Must be sure it's either detailed or quick",
#                     },
#                 },
#             "required": ["report_type"],
#             },
#         }
#     },
#     {
#     "type": "function",
#         "function": {
#         "name": "set_company",
#         "description": "Call this every time the user gives you a company name",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "company": {
#                     "type": "string",
#                     "description": "The company name",
#                     },
#                 },
#             "required": ["company"],
#             },
#         }
#     },
#     {
#     "type": "function",
#         "function": {
#         "name": "set_report_ready",
#         "description": "At the end of a conversation. When the user tells you they have given you all the information and are ready for the report. This function shows them the report.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "is_ready": {
#                     "type": "string",
#                     "description": "True or False: is the user ready to generate the report?",
#                     },
#                 },
#             "required": ["is_ready"],
#             },
#         }
#     },
#     {
#     "type": "function",
#         "function":
#         {
#         "name": "set_new",
#         "description": "Call this when the user is finished with the report and has no more changes.",
#         }
#     },
#     {
#     "type": "function",
#         "function": {
#         "name": "set_context",
#         "description": "Sets the context or lack of context",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "context": {
#                     "type": "string",
#                     "description": "Either context or NA",
#                     },
#                 },
#             "required": ["context"],
#             },
#         }
#     }
 
# ]
 
# #run_insights_assistant()