from typing import List, Tuple
from app.utils.vector_store import vector_db
import logging
from app.utils.vector_store import retriever
from fuzzywuzzy import fuzz

def get_default_destination() -> List[Tuple[str, str]]:
    try:
        # Query the vector store for documents
        results = vector_db.similarity_search(
            "JLR lodge",
            k=500  # Retrieve more documents than needed to ensure we have enough after filtering
        )

        # Filter and process the results
        filtered_destinations = {}
        for doc in results:
            
            primary_key = doc.metadata.get('eoexperience_primary_key')
            display_priority = doc.metadata.get('display_priority')
            eoexperience_name = doc.metadata.get('eoexperience_name', 'Unknown')
            lkdestination_name = doc.metadata.get('lkdestination_name', 'Unknown')

            # Only consider documents with display_priority < 3 and valid primary key
            if (primary_key and display_priority     and display_priority < 2):
                # print('\n',doc,'\n')
                # If this primary key is not yet in our dictionary or has a lower display_priority
                if (primary_key not in filtered_destinations or
                    display_priority < filtered_destinations[primary_key][1]):
                    filtered_destinations[primary_key] = (eoexperience_name, lkdestination_name, display_priority)

        # Sort the destinations by display_priority and take the top 10
        sorted_destinations = sorted(filtered_destinations.values(), key=lambda x: x[2])[:10]
        print('\nreturn get_default_destination\n')
        # Return the list of tuples (eoexperience_name, lkdestination_name)
        return [(eo_name, lk_name) for eo_name, lk_name, _ in sorted_destinations]

    except Exception as e:
        logging.error(f"Error retrieving default destinations: {e}")
        return []

def retrieve_and_filter_documents(query, context_analysis):
    try:
# Check if there's a topic switcpri
        print('\nretrieve_and_filter_documents\n:')
        # if "Topic Switch: Yes" in context_analysis:
        #     # If there's a topic switch, only use the query for retrieval
        #     relevant_chunks = retriever.get_relevant_documents(query)
        # else:
        #     # If no topic switch, use both query and context analysis for retrieval
        #     combined_query = f"{query}\n\nContext: {context_analysis}"
        # print('p')
        # print(query)
        # print('dd')
        
        relevant_chunks = retriever.invoke(query)

        if relevant_chunks:
            sorted_documents = sorted(relevant_chunks, key=lambda x: x.metadata.get('display_priority', float('inf')))

            # Further filter and rank documents based on the relevance of `eoexperience_name` to the query
            ranked_documents = []
            for doc in sorted_documents:
                eoexperience_name = doc.metadata.get('eoexperience_name', 'Unknown')
                relevance_score = fuzz.partial_ratio(query.lower(), eoexperience_name.lower())
                ranked_documents.append((doc, relevance_score))

            # Sort by relevance score in descending order and take the top 3
            ranked_documents = sorted(ranked_documents, key=lambda x: x[1], reverse=True)[:3]

            # Extract the top 3 documents
            top_documents = [doc for doc, score in ranked_documents]

            # Create the context string from the top 3 documents
            context = "\n".join([f"{doc.metadata.get('eoexperience_name')} {doc.metadata.get('lkdestination_name')}\n{doc.page_content}" for doc in top_documents])

            return context, top_documents


        return None, []
    except Exception as e:
        logging.error(f"Error retrieving and filtering documents: {e}")
        raise
