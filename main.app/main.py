import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
import os
import openai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import cloudscraper
import time
from tiktoken import Tokenizer
from tiktoken import Tokenizer

def google_search(search_term, api_key, cse_id, num_results=10, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, num=num_results, **kwargs).execute()
    return res['items']

def fetch_and_parse_html(url):
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(['script', 'style']):
            script.extract()
        text = soup.get_text()
        clean_text = " ".join(text.split())
        return clean_text
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        with open("failed_urls.txt", "a") as f:
            f.write(url + '\n')
        return None
    except cloudscraper.CloudflareChallengeError:
        print("Cloudflare protection detected, skipping URL.")
        with open("failed_urls.txt", "a") as f:
            f.write(url + '\n')
        return None

def process_search(search_term, num_results):
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    results = google_search(search_term, api_key, cse_id, num_results=num_results)

    vectorizer = TfidfVectorizer()
    all_texts = []
    all_urls = []

    for i, result in enumerate(results):
        url = result['link']
        clean_text = fetch_and_parse_html(url)
        if clean_text:
            messages = [
                {"role": "system", "content": "You are a skilled information gatherer. Organize the information from the user and extract meaningful data from the webpage."},
                {"role": "user", "content": clean_text}
            ]

            openai.api_key = OPENAI_API_KEY
            completion = openai.ChatCompletion.create(
              model="gpt-3.5-turbo-16k",
              messages=messages,
              max_tokens=1500  # Limit the maximum number of tokens
            )

            extracted_info = completion.choices[0].message['content']

            # Store the original text and extracted info
            save_path = "C:\\Users\\81905\\Downloads\\info\\"
            if not os.path.exists(save_path):
                os.makedirs(save_path)

            # Check for similarity with previous texts
            if all_texts:
                vectorizer.fit_transform(all_texts + [clean_text])
                current_text_vector = vectorizer.transform([clean_text])
                similarities = cosine_similarity(current_text_vector, vectorizer.transform(all_texts))
                similar_index = next((index for index, similarity in enumerate(similarities[0]) if similarity > 0.8), None)
            else:
                similar_index = None

            if similar_index is not None:
                # If a similar text is found, append to the existing file
                with open(os.path.join(save_path, f"extracted_info_{similar_index}.txt"), "a", encoding="utf-8") as f:
                    f.write(f"\n\nURL: {url}\n")
                    f.write(extracted_info)
            else:
                # If no similar text is found, create new files
                with open(os.path.join(save_path, f"original_info_{i}.txt"), "w", encoding="utf-8") as f:
                    f.write(f"URL: {url}\n")
                    f.write(clean_text)
                with open(os.path.join(save_path, f"extracted_info_{i}.txt"), "w", encoding="utf-8") as f:
                    f.write(f"URL: {url}\n")
                    f.write(extracted_info)

                # Update the all_texts and all_urls lists
                all_texts.append(clean_text)
                all_urls.append(url)

        # Return the progress and completion status
        progress_status = f"Processing result {i + 1}/{len(results)}"
        completion_status = f"Completed processing result {i + 1}/{len(results)}"
        
        # Add a delay to avoid sending too many requests at once
        time.sleep(5)

        # Compute token count with tiktoken
        tokenizer = Tokenizer()
        token_count = tokenizer.count_tokens(extracted_info)

        return progress_status, completion_status, token_count
        