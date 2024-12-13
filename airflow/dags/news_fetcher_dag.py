from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import sys
import json
from qdrant_client import QdrantClient
from openai import OpenAI
import openai


# Add the plugins path for custom imports
sys.path.append('/opt/airflow/plugins')
from news_fetcher import fetch_news
from push_to_qdrant import push_to_qdrant

# Default DAG arguments
default_args = {
    'owner': 'ajinabraham',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


# Function to generate embedding using OpenAI

#def get_embedding(text, model="text-embedding-ada-002"):
 #   """
  #  #Generate embeddings for the given text using OpenAI API.
   # """
    #try:
     #   response = openai.Embedding.create(
      #      input=text,
       #     model=model
        #)
        #return response['data'][0]['embedding']
    #except Exception as e:
     #   raise RuntimeError(f"Error generating embedding: {e}")


# GPT Task: Query Qdrant and feed to GPT
def query_qdrant_and_gpt(**kwargs):
    """
    Query Qdrant for relevant articles and feed them to GPT for text generation or question answering.
    Save the GPT response to a JSON file.
    """
    # Initialize Qdrant client
    qdrant_client = QdrantClient(
        api_key=os.getenv("QDRANT_API_KEY"),
        url=os.getenv("QDRANT_API_URL"),
    )
    collection_name = "news_collection"

    # Define query (customize this)
    query_text = kwargs.get('query', "university")
    #query_vector = get_embedding(query_text, model="text-embedding-ada-002")
    # Search Qdrant for relevant embeddings
    search_results = qdrant_client.search(
        collection_name=collection_name,
        query_vector=[0] * 1536,  # Replace with actual query vector
        #query_vector=query_vector,
        limit=5,
    )

    # Extract content for GPT
    retrieved_articles = [
        point.payload.get("title", "") + " " + point.payload.get("description", "")
        for point in search_results
    ]
    input_text = "\n".join(retrieved_articles)

    # Initialize OpenAI GPT client
    gpt_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Generate GPT response
    response = gpt_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an assistant summarizing news."},
            {"role": "user", "content": input_text},
        ],
    )

    # Extract GPT response content
    gpt_response = response.choices[0].message.content

    # Save GPT response to a file
    gpt_response_path = "/opt/airflow/logs/gpt_response.json"
    with open(gpt_response_path, 'w') as f:
        json.dump({"response": gpt_response}, f, indent=4)

    print(f"GPT Response saved to {gpt_response_path}")

# Define the DAG
with DAG(
    'news_fetcher_with_gpt',
    default_args=default_args,
    description='A DAG to fetch news, generate embeddings, and feed data to GPT',
    schedule_interval='@daily',
    start_date=datetime(2023, 12, 10),
    catchup=False,
) as dag:
    # Task to fetch news
    fetch_news_task = PythonOperator(
        task_id='fetch_news',
        python_callable=fetch_news,
    )

    # Task to push data to Qdrant
    push_to_qdrant_task = PythonOperator(
        task_id='push_to_qdrant',
        python_callable=push_to_qdrant,
    )

    # Task to query Qdrant and feed to GPT
    query_gpt_task = PythonOperator(
        task_id='query_qdrant_and_gpt',
        python_callable=query_qdrant_and_gpt,
        provide_context=True,
    )

    # Define task dependencies
    fetch_news_task >> push_to_qdrant_task >> query_gpt_task
