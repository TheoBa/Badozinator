import requests
from requests.auth import HTTPBasicAuth
import streamlit as st
import os
import json
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils.documents import process_document


def preprocess_confluence_html(html_content, title, fileId, parentId):
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove navigation, headers, footers, comments, etc.
    for div in soup.find_all(['nav', 'header', 'footer', 'script', 'style']):
        div.decompose()
    
    # Optional: Remove specific Confluence classes
    for div in soup.find_all(class_=re.compile(r'confluence-|aui-|header-|footer-')):
        div.decompose()
    
    # Extract main content
    main_content = soup.find('div', {'id': 'main-content'}) or soup
    
    # Get plain text and clean it
    text = main_content.get_text(separator=' ', strip=True)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Create structured output
    document = {
        "title": title,
        "content": text,
        "id": fileId,
        "parent_id": parentId,
    }
    
    return document

def process_directory(directory_path, output_file):
    documents = []
    
    for filename in os.listdir(directory_path):
        if filename.endswith('.html'):
            file_path = os.path.join(directory_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
                document = preprocess_confluence_html(
                    html_content, 
                    title=filename.split("_")[2],
                    fileId=filename.split("_")[0], 
                    parentId=filename.split("_")[1]
                    )
                documents.append(document)
    
    # Save to JSON file (for RAG ingestion)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    # Initialize document metadata if not exists
    if "document_metadata" not in st.session_state:
        st.session_state.document_metadata = {}
        
    for doc in documents:
        file_path = f"data/documents/{doc['title']}.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(doc['content'])
        
        st.session_state.document_metadata[f"{doc["title"]}.txt"] = {
            "original_name": doc["title"],
            "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "size": len(doc["content"]),
            "status": "uploaded",
            "processing_error": None
        }
    
        splits = process_document(file_path)
    
    # Mark documents as processed
    st.session_state.documents_processed = True

    return documents

def fetch_confluence_pages():
    # Create a directory to store the pages
    output_dir = "./confluence_pages"
    os.makedirs(output_dir, exist_ok=True)

    your_domain = "alten-mdc.atlassian.net"
    spaceId = 2182709250
    get_pages_from_spaceId_url = f"https://{your_domain}/wiki/api/v2/spaces/{spaceId}/pages?limit=250&body-format=storage"
    username = "theo.badoz@alten.com"
    api_token = st.secrets["confluence_api_token"]
    headers = {
        "Accept": "application/json"
    }

    # Fetch all pages in the specified space
    response = requests.get(
        url=get_pages_from_spaceId_url,
        headers=headers,
        auth=HTTPBasicAuth(username, api_token)
    )

    if response.status_code == 200:
        response_json = json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": "))
        response_json = json.loads(response.text)['results']

    with st.spinner(f"Downloading confluence for space {spaceId}"):
        for id, page in enumerate(response_json):
            title = page['title']
            page_id = page['id']
            parent_id = page['parentId']
            body = page['body']['storage']['value']
            st.write(f"Saving {title}...{id + 1}/{len(response_json)}")
            try:
                save_html(body, f"{output_dir}/{page_id}_{parent_id}_{title}.html")
            except Exception as e:
                st.error(f"Error saving {title}: {e}")
                continue
        st.success("Done!")
        
def save_html(content, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

# if __name__ == "__main__":
#     fetch_confluence_pages()