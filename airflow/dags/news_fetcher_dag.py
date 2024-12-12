import json
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import os
import logging

# Add the directory containing custom plugins to the Python path
sys.path.append('/opt/airflow/plugins')  # Adjust path to match the container environment

from news_fetcher import fetch_news
from push_to_qdrant import push_to_qdrant

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default DAG arguments
default_args = {
    'owner': 'ajinabraham',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,  # Increase retries for robustness
    'retry_delay': timedelta(minutes=2),
}

# Define task to fetch news articles
def fetch_news_task(**kwargs):
    """Fetch news and save to a shared JSON file."""
    try:
        query = "Northeastern University Boston"
        country = "us"
        # Construct the output path dynamically
        airflow_home = os.getenv("AIRFLOW_HOME", "/opt/airflow")
        output_path = os.path.join(airflow_home, "logs", "news_output.json")
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Fetch articles and save them
        articles = fetch_news(query=query, country=country)
        with open(output_path, 'w') as f:
            json.dump(articles, f, indent=4)
        logger.info(f"Saved news to {output_path}")
    except Exception as e:
        logger.error(f"Error in fetch_news_task: {e}")
        raise

# Define the DAG
with DAG(
    dag_id='news_fetcher_dag',
    default_args=default_args,
    description='A DAG to fetch news articles and push them to Qdrant',
    schedule_interval='@daily',
    start_date=datetime(2023, 12, 10),
    catchup=False,
) as dag:
    # Task to fetch news
    fetch_news_operator = PythonOperator(
        task_id='fetch_news_task',
        python_callable=fetch_news_task,
        provide_context=True,  # Allows access to **kwargs in the function
        execution_timeout=timedelta(minutes=5),  # Add a timeout to limit execution time
    )

    # Task to push data to Qdrant
    push_to_qdrant_operator = PythonOperator(
        task_id='push_to_qdrant_task',
        python_callable=push_to_qdrant,  # Ensure this function is properly implemented
        execution_timeout=timedelta(minutes=10),  # Add a timeout to prevent hanging
    )

    # Define the task dependencies
    fetch_news_operator >> push_to_qdrant_operator
