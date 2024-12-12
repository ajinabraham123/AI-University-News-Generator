import streamlit as st
from PIL import Image  # For logo and other static images
from dotenv import load_dotenv
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'airflow/plugins'))
from news_fetcher import fetch_news  # Import the fetch_news function from your news_fetcher script
import json

# Load environment variables
load_dotenv()

# Access the NEWSAPI_KEY variable (Ensure .env is properly configured)
api_key = os.getenv("NEWSAPI_KEY")

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

# News Generator Page
def news_generator():
    st.title("Personalized News Generator")
    query = st.text_input("Search News", placeholder="Type a keyword (e.g., Scholarships)")
    country = st.selectbox("Country", ["us", "in", "gb", "ca", "au"], index=0)

    if st.button("Generate News"):
        with st.spinner("Fetching news..."):
            try:
                articles = fetch_news(query=query, country=country)
                st.success(f"Found {len(articles)} articles!")
                for idx, article in enumerate(articles, start=1):
                    st.markdown(f"### {idx}. [{article['title']}]({article['url']})")
                    st.write(f"**Source**: {article['source']}")
                    st.write(article['description'])
                    st.write("---")
            except Exception as e:
                st.error(f"An error occurred: {e}")

    # Display previously fetched news
    st.subheader("Previously Fetched News")
    try:
        with open('/Users/ajinabraham/Desktop/AI-University-News-Generator/dags/news_output.json') as f:
            saved_articles = json.load(f)
            for idx, article in enumerate(saved_articles, start=1):
                st.markdown(f"### {idx}. [{article['title']}]({article['url']})")
                st.write(f"**Source**: {article['source']}")
                st.write(article['description'])
                st.write("---")
    except FileNotFoundError:
        st.info("No previously fetched news found.")


# Upload Data Page
def upload_data():
    st.title("Upload Data")
    st.write("Upload documents or flyers to include in the news feed.")
    
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt", "docx"])
    if uploaded_file:
        st.success(f"File {uploaded_file.name} uploaded successfully.")
        st.info("Data processing functionality will be integrated here.")

# Settings Page


# About Page
def about_page():
    st.title("About This Project")
    st.write("""
    The AI University News Generator is designed to provide students with personalized, 
    real-time updates about campus life. Using cutting-edge AI and NLP technologies, 
    this platform consolidates data from multiple sources into concise, actionable news.
    """)
    st.write("Learn more about how it works and our mission.")

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