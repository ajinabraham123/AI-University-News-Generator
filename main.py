import streamlit as st
from PIL import Image  # For logo and other static images
from dotenv import load_dotenv
import os
from news_fetcher import fetch_news  # Import the fetch_news function from your news_fetcher script

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
    page = st.sidebar.radio("Go to", ["Home", "News Generator", "Upload Data", "Settings", "About"])
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
    st.write("Search and explore news tailored to your preferences.")
    
    query = st.text_input("Search News", placeholder="Type a keyword or query (e.g., 'Scholarships', 'Events')")
    country = st.selectbox("Country", ["us", "in", "gb", "ca", "au"], index=0)  # Default to 'us'

    if st.button("Generate News"):
        if not query:
            st.warning("Please enter a query to fetch news.")
        else:
            with st.spinner("Fetching news articles..."):
                news_articles = fetch_news(query=query, country=country)

            if news_articles:
                st.subheader("Top News Articles")
                for idx, article in enumerate(news_articles, start=1):
                    st.markdown(f"### {idx}. [{article['title']}]({article['url']})")
                    st.write(f"**Source**: {article['source']}")
                    st.write(article['description'])
                    st.write("---")
            else:
                st.warning("No articles found. Try adjusting your search terms.")



# Upload Data Page
def upload_data():
    st.title("Upload Data")
    st.write("Upload documents or flyers to include in the news feed.")
    
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt", "docx"])
    if uploaded_file:
        st.success(f"File {uploaded_file.name} uploaded successfully.")
        st.info("Data processing functionality will be integrated here.")

# Settings Page
def settings_page():
    st.title("Settings")
    st.write("Configure your preferences.")
    
    user_email = st.text_input("Email", placeholder="Enter your email for personalized updates")
    frequency = st.selectbox("Update Frequency", ["Daily", "Weekly", "Monthly"])
    
    if st.button("Save Settings"):
        st.success("Settings saved successfully.")

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
    elif page == "Upload Data":
        upload_data()
    elif page == "Settings":
        settings_page()
    elif page == "About":
        about_page()

if __name__ == "__main__":
    main()
