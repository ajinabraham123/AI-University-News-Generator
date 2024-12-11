import json
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from news_fetcher import fetch_news
import sys
import os

# Add the directory containing news_fetcher.py to the Python path
sys.path.append('/Users/ajinabraham/Desktop/AI-University-News-Generator/plugins')

from news_fetcher import fetch_news

default_args = {
    'owner': 'ajinabraham',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def fetch_news_task():
    """Fetch news and save to a shared JSON file."""
    query = "University"
    country = "us"
    articles = fetch_news(query=query, country=country)
    output_path = '/opt/airflow/logs/news_output.json'
    with open(output_path, 'w') as f:
        json.dump(articles, f, indent=4)
    print(f"Saved news to {output_path}")

with DAG(
    dag_id='news_fetcher_dag',
    default_args=default_args,
    description='A DAG to fetch news articles',
    schedule_interval='@daily',
    start_date=datetime(2023, 12, 10),
    catchup=False,
) as dag:
    fetch_news_operator = PythonOperator(
        task_id='fetch_news_task',
        python_callable=fetch_news_task,
    )

    fetch_news_operator
