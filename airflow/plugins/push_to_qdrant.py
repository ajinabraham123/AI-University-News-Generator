import os
import json
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_embeddings(text):
    """
    Generate embeddings for the input text using OpenAI GPT API.
    """
    try:
        # Generate embedding using OpenAI client
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=[text]  # Input must be a list
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        raise

def push_to_qdrant():
    """
    Push news articles to Qdrant with generated embeddings.
    """
    # Qdrant connection details from environment variables
    API_URL = os.getenv("QDRANT_API_URL")
    API_KEY = os.getenv("QDRANT_API_KEY")

    if not API_URL or not API_KEY:
        raise ValueError("Qdrant API URL or API Key is not set in the environment variables")

    # Initialize Qdrant client
    client = QdrantClient(API_URL, api_key=API_KEY)

    # Collection name and vector size
    COLLECTION_NAME = "news_collection"
    VECTOR_SIZE = 1536  # Vector size for "text-embedding-ada-002"

    # Define vector configuration
    vector_config = VectorParams(size=VECTOR_SIZE, distance="Cosine")

    # Create or recreate the collection
    try:
        if client.get_collection(COLLECTION_NAME):
            client.delete_collection(COLLECTION_NAME)
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=vector_config
        )
        print(f"Collection '{COLLECTION_NAME}' created successfully.")
    except Exception as e:
        raise RuntimeError(f"Error creating collection in Qdrant: {e}")

    # Path to the JSON file
    json_file_path = "./news_output.json"  # Update path as per your setup

    # Load the JSON data
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"JSON file not found at {json_file_path}")

    with open(json_file_path, "r") as f:
        articles = json.load(f)

    # Prepare points for insertion into Qdrant
    points = []
    for idx, article in enumerate(articles):
        # Combine title and description for embedding generation
        content = (article.get("title", "") + " " + article.get("description", "")).strip()
        
        # Skip if there is no meaningful content
        if not content:
            continue
        
        # Generate embeddings using OpenAI GPT
        try:
            vector = generate_embeddings(content)
        except Exception as e:
            print(f"Failed to generate embeddings for article {idx + 1}: {e}")
            continue

        # Create a point with article details as payload
        points.append(
            PointStruct(
                id=idx + 1,
                vector=vector,
                payload={
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "url": article.get("url"),
                    "source": article.get("source"),
                }
            )
        )

    # Insert data into Qdrant
    if points:
        try:
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            print(f"Data pushed to Qdrant successfully with {len(points)} articles!")
        except Exception as e:
            raise RuntimeError(f"Error pushing data to Qdrant: {e}")
    else:
        print("No valid articles found to push to Qdrant.")

# Call the function for testing or integration
if __name__ == "__main__":
    push_to_qdrant()
