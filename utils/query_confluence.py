import requests
from requests.auth import HTTPBasicAuth
import streamlit as st
import os
import json

def get_pages_ids(spaceId):
    your_domain = "alten-mdc.atlassian.net"
    get_pages_from_spaceId_url = f"https://{your_domain}/wiki/api/v2/spaces/{spaceId}/pages"
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
        st.json(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))


def fetch_confluence_pages():
    your_domain = "alten-mdc.atlassian.net"
    spaceKey = "PRA"
    spaceId = 2182709250
    # Replace with your Confluence URL, username, and API token
    get_pages_from_spaceId_url = f"https://{your_domain}/wiki/api/v2/spaces/{spaceId}/pages?limit=250&body-format=atlas_doc_format"
    get_space_id_url = f"https://{your_domain}/wiki/rest/api/space/{spaceKey}"
    confluence_url = f"https://{your_domain}/wiki/rest/api/space/{spaceKey}/content"
    confluence_url_v2 = f"https://{your_domain}/wiki/api/v2/pages/{id}?body-format={1}"
    next_url = f"https://{your_domain}/wiki/api/v2/spaces/2182709250/pages?cursor=eyJpZCI6IjIyMTEwODYzMzgiLCJjb250ZW50T3JkZXIiOiJpZCIsImNvbnRlbnRPcmRlclZhbHVlIjoyMjExMDg2MzM4fQ=="
    username = "theo.badoz@alten.com"
    api_token = st.secrets["confluence_api_token"]
    space_key = "PRA"

    # Create a directory to store the pages
    output_dir = "./confluence_pages"
    os.makedirs(output_dir, exist_ok=True)

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
        st.json(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
        
        #pages = response.json()["results"]
        


    if response.status_code == 200:
        pages = response.json()["results"]
        for page in pages:
            page_id = page['id']
            page_title = page['title'].replace('/', '_')  # Replace slashes to avoid file issues

            # Fetch the content of each page
            content_response = requests.get(
                f"{confluence_url}/rest/api/content/{page_id}?expand=body.storage",
                auth=HTTPBasicAuth(username, api_token)
            )

            if content_response.status_code == 200:
                content = content_response.json()["body"]["storage"]["value"]
                # Save the content to a text file
                with open(os.path.join(output_dir, f"{page_title}.txt"), "w", encoding="utf-8") as file:
                    file.write(content)
                st.write(f"Saved: {page_title}.txt")
            else:
                print(f"Failed to fetch content for page {page_title}: {content_response.status_code} - {content_response.text}")
    else:
        st.write(f"Failed to fetch pages: {response.status_code} - {response.text}")

if __name__ == "__main__":
    fetch_confluence_pages()