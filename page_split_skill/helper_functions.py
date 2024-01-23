import re
from azure.storage.blob import BlobServiceClient, BlobClient
from .app_settings import *


def download_blobs_to_string(blob_service_client: BlobServiceClient, container_name: str) -> (list):
    container_client = blob_service_client.get_container_client(container=INPUT_CONTAINER_NAME)
    blob_docs = container_client.list_blob_names()
    
    downloaded_texts = []
    
    for blob_name in blob_docs:
        blob_client = blob_service_client.get_blob_client(container=INPUT_CONTAINER_NAME, blob=blob_name)
        downloader = blob_client.download_blob(max_concurrency=1, encoding='utf-8')
        blob_text = downloader.readall()
        downloaded_texts.append((blob_name, blob_text))
        #split_markdown_by_headings(blob_text, blob_name)
    return downloaded_texts


def split_markdown_by_headings(doc_title: str, markdown_content: str) -> list:
  # Define the regular expression pattern to match H1 and H2 headings
  pattern = r'((?<!#)#{1,2}(?!#).*)'

  # Split the Markdown text based on the headings
  sections = re.split(pattern, markdown_content)
  
  
  url = sections[0]
  sections = sections[1:]
  # Combine each heading with its corresponding text
  combined_sections = []
  for i in range(0, len(sections), 2):
    heading = sections[i].strip()  # Get the heading from sections[i]
    heading = heading.replace("#", "")
    text = sections[i + 1].strip() if i + 1 < len(
        sections) else ''  # Get the text from sections[i + 1] if it exists, otherwise use an empty string
    
    output_content_chunk = str(url) + "\n" + str(text)
    
    chunk_title = doc_title.replace(".txt", (" --" + str(heading) + ".txt"))
    doc_chunk_tup = (chunk_title, output_content_chunk)
    combined_sections.append(doc_chunk_tup)  # Add the combined section to the list

  return combined_sections
