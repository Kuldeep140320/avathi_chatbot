import os
import psycopg2
import pandas as pd
from langchain_community.embeddings import HuggingFaceEmbeddings
import faiss
import numpy as np
import json
from dotenv import load_dotenv
import sys


# Load environment variables
load_dotenv()

# Database connection
def get_data_from_postgres(query):
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        dbname=os.getenv('DB_NAME', 'dbname'),
        user=os.getenv('DB_USER', 'user'),
        password=os.getenv('DB_PASSWORD', 'password')
    )
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Fetch data
query = "SELECT primary_key, name, description FROM eoexperience WHERE is_active = TRUE"
experiences_df = get_data_from_postgres(query)

# Vectorize descriptions
model = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
experience_vectors = model.embed_texts(experiences_df['description'].tolist())

# Create Faiss index
dimension = experience_vectors.shape[1]
index = faiss.IndexFlatL2(dimension)
experience_vectors = np.array(experience_vectors, dtype='float32')
index.add(experience_vectors)
# print("experiences_df")
# sys.exit()
# Save the index and metadata
faiss.write_index(index, 'bookingChainExpTicket-all-MiniLM-L6-v2.index')
metadata = experiences_df[['primary_key', 'name']].to_dict(orient='records')
with open('bookingChainExpTicket-all-MiniLM-L6-v2_metadata.json', 'w') as f:
    json.dump(metadata, f)

print("Faiss index and metadata saved successfully.")
