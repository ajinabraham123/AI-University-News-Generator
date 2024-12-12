import streamlit as st
from PIL import Image  # For logo and other static images
from dotenv import load_dotenv
import os
import sys
import requests
import json
import time

# Add the plugins path for custom imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'airflow/plugins'))
from news_fetcher import fetch_news  # Import the fetch_news function from your news_fetcher script

# Load environment variables
load_dotenv()

# Access environment variables
api_key = os.getenv("NEWSAPI_KEY")
airflow_base_url = os.getenv("AIRFLOW_BASE_URL", "http://localhost:8080/api/v1")
airflow_username = os.getenv("AIRFLOW_USERNAME", "airflow")
airflow_password = os.getenv("AIRFLOW_PASSWORD", "airflow")

# Check if API key is loaded
if not api_key:
    st.error("API key for NewsAPI is missing. Please check your .env file.")

# Global configuration
st.set_page_config(page_title="AI University News Generator", layout="wide")

# Sidebar Navigation
def sidebar():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "News Generator", "About"])
    return page

# Home Page
def home_page():
    st.title("AI University News Generator")
    st.subheader("Stay informed with personalized, real-time campus updates!")
    st.write("This platform delivers curated news, safety alerts, and academic opportunities tailored to your interests.")
    try:
        st.image("images/news_portal.webp", use_column_width=True)  # Replace with your image file path
    except FileNotFoundError:
        st.warning("Image not found. Please ensure the 'images/news_portal.webp' file exists.")

# Check Airflow Connectivity
def check_airflow_connection():
    try:
        response = requests.get(f"{airflow_base_url}/dags", auth=(airflow_username, airflow_password))
        response.raise_for_status()
        st.success("Connected to Airflow API!")
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to Airflow API: {e}")
        return False

# Trigger Airflow DAG
def trigger_airflow_dag(dag_id, query, country):
    url = f"{airflow_base_url}/dags/{dag_id}/dagRuns"
    payload = {"conf": {"query": query, "country": country}}
    try:
        response = requests.post(url, auth=(airflow_username, airflow_password), json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        st.error(f"An error occurred: {err}")
    return None

# Check DAG Run Status
def check_dag_run_status(dag_id, dag_run_id):
    url = f"{airflow_base_url}/dags/{dag_id}/dagRuns/{dag_run_id}"
    try:
        response = requests.get(url, auth=(airflow_username, airflow_password))
        response.raise_for_status()
        return response.json().get("state")
    except Exception as e:
        st.error(f"Error checking DAG run status: {e}")
        return None

# Display Results
def display_results():
    st.subheader("GPT Response")
    gpt_response_path = "airflow/logs/gpt_response.json"
    try:
        if os.path.exists(gpt_response_path):
            with open(gpt_response_path) as f:
                gpt_data = json.load(f)
                st.write(gpt_data.get("response", "No response found."))
        else:
            st.error(f"GPT response file not found at {gpt_response_path}.")
    except Exception as e:
        st.error(f"Error reading GPT response: {e}")

    st.subheader("Previously Fetched News")
    news_output_path = "airflow/logs/news_output.json"
    try:
        if os.path.exists(news_output_path):
            with open(news_output_path) as f:
                saved_articles = json.load(f)
                for idx, article in enumerate(saved_articles, start=1):
                    st.markdown(f"### {idx}. [{article['title']}]({article['url']})")
                    st.write(f"**Source**: {article['source']}")
                    st.write(article['description'])
                    st.write("---")
        else:
            st.error(f"News output file not found at {news_output_path}.")
    except Exception as e:
        st.error(f"Error reading news output: {e}")

# News Generator Page
def news_generator():
    st.title("Personalized News Generator")

    # Connectivity Check
    if not check_airflow_connection():
        return

    query = st.text_input("Search News", placeholder="Type a keyword (e.g., Scholarships)")
    country = st.selectbox("Country", ["us", "in", "gb", "ca", "au"], index=0)

    if st.button("Generate News"):
        with st.spinner("Triggering Airflow DAG to fetch and process news..."):
            if query:
                response = trigger_airflow_dag("news_fetcher_with_gpt", query, country)
                if response:
                    st.success("Airflow DAG triggered successfully! Polling for status...")
                    dag_run_id = response.get("dag_run_id")

                    # Poll for status
                    status = "queued"
                    while status in ["queued", "running"]:
                        time.sleep(5)  # Wait before polling again
                        status = check_dag_run_status("news_fetcher_with_gpt", dag_run_id)
                        st.info(f"DAG Run Status: {status}")

                    if status == "success":
                        st.success("DAG execution completed successfully!")
                        display_results()
                    else:
                        st.error(f"DAG execution failed or did not complete. Status: {status}")
                else:
                    st.error("Failed to trigger Airflow DAG.")
            else:
                st.warning("Please enter a query before triggering the DAG.")

# About Page
def about_page():
    st.title("About This Project")
    st.write("""
    The AI University News Generator provides personalized updates about campus life using cutting-edge AI and NLP.
    """)

# Main Application
def main():
    page = sidebar()

    if page == "Home":
        home_page()
    elif page == "News Generator":
        news_generator()
    elif page == "About":
        about_page()

if __name__ == "__main__":
    main()