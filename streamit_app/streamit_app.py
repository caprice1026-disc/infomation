import streamlit as st
import sys
sys.path.append('../main_app')
from main import process_search

st.title("Web Information Extractor")

search_term = st.text_input("Enter a search term:", value="ED 自由診療")
num_results = st.number_input("Number of results to fetch:", min_value=1, max_value=100, value=10)

if st.button("Search"):
    progress_status, completion_status = process_search(search_term, num_results)
    st.write(progress_status)
    st.write(completion_status)

if st.button("Search"):
    progress_status, completion_status, token_count = process_search(search_term, num_results)
    st.write(progress_status)
    st.write(completion_status)
    st.write(f'Token Count: {token_count}')