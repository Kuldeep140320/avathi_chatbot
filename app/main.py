import os
import sys
import logging
import streamlit as st
from dotenv import load_dotenv

# Ensure the correct path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.faiss_helper import initialize_vector_store
from app.services.nlp import get_chain
from app.services.nlp2 import handle_query  

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize session state for conversation history
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

def main():
    st.title("Chatbot Data and Chain Flow Visualization")

    # Initialize vector store
    with st.sidebar:
        st.header("Settings")
        vector_db_file_path = st.text_input("Vector Store Path", "vector_store_new2")
        if st.button("Initialize Vector Store"):
            logging.debug(f"Initializing vector store with path: {vector_db_file_path}")
            try:
                vector_store = initialize_vector_store(vector_db_file_path)
                st.success("Vector store initialized.")
                st.write(f"Vector store details: {vector_store}")
            except Exception as e:
                st.error(f"Error initializing vector store: {e}")

    query = st.text_input("Enter your query", placeholder="Type your query here...")

    if st.button("Send"):
        logging.debug(f"Query: {query}")
        logging.debug("Getting the chain for vector store")
        try:
            # chain = get_chain(vector_db_file_path)
            # result = chain.invoke(query)
            result = handle_query(query)
            logging.info(f"Query: {query}")
            logging.info(f"Result: {result}\n")

            # Add the interaction to the conversation history
            st.session_state.conversation_history.append(("user", query))
            st.session_state.conversation_history.append(("bot", result['result']))

            # Display the conversation history
            st.subheader("Conversation History")
            for i, (sender, message_text) in enumerate(st.session_state.conversation_history):
                if sender == "user":
                    st.markdown(f"**You:** {message_text}")
                else:
                    st.markdown(f"**Bot:** {message_text}")

            # Display detailed information
            with st.expander("Detailed Information", expanded=False):
                st.subheader("Source Documents")
                for j, doc in enumerate(result['source_documents']):
                    st.markdown(f"##### Document {j + 1} Metadata")
                    for key, value in doc.metadata.items():
                        st.markdown(f"**{key.capitalize()}:** {value}")
                    st.markdown("##### Document Content")
                    st.markdown(doc.page_content.replace('\n', '\n\n'))

        except Exception as e:
            st.error(f"Error invoking chain: {e}")

if __name__ == "__main__":
    main()
