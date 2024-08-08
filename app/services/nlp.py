# import os
# from langchain.prompts import PromptTemplate
# from langchain.chains import RetrievalQA
# from langchain_community.vectorstores import FAISS
# from langchain_openai import OpenAI
# from langchain_huggingface import HuggingFaceEmbeddings
# import sys
# embedding_model = "all-MiniLM-L6-v2"
# instruct_embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

# def get_chain(vector_db_file_path):
#     """Create the RetrievalQA chain."""
#     vector_db = FAISS.load_local(vector_db_file_path, embeddings=instruct_embeddings, allow_dangerous_deserialization=True)
#     retriever = vector_db.as_retriever(search_kwargs={"k": 2})
#     # print(retriever)
#     # sys.exit()
#     prompt_template = """Given the following context and a question, generate an answer based on this context only.
#     If the answer is not directly found in the context, try to infer a relevant answer based on the available information.
#     If no relevant information is found, kindly state "I don't have enough information to provide an answer."

#     CONTEXT: {context}

#     QUESTION: {question}"""
#     PROMPT = PromptTemplate(
#         template=prompt_template, input_variables=["context", "question"]
#     )

#     chain = RetrievalQA.from_chain_type(
#         llm=OpenAI(api_key=os.environ['OPENAI_API_KEY'], temperature=0.6),
#         chain_type="stuff",
#         retriever=retriever,
#         input_key="query",
#         return_source_documents=True,
#         chain_type_kwargs={"prompt": PROMPT}
#     )
#     print(chain)
#     return chain
