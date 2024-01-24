import re
from azure.storage.blob import BlobServiceClient, BlobClient
from .app_settings import *
from datetime import datetime
from pytz import timezone

blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)

def download_blobs_to_string(blob_service_client: BlobServiceClient, container_name: str) -> (list):
  container_client = blob_service_client.get_container_client(container=INPUT_CONTAINER_NAME)
  blob_docs = container_client.list_blob_names()

  downloaded_texts = []

  for blob_name in blob_docs:
      blob_client = blob_service_client.get_blob_client(container=INPUT_CONTAINER_NAME, blob=blob_name)
      downloader = blob_client.download_blob(max_concurrency=1, encoding='utf-8')
      blob_text = downloader.readall()
      downloaded_texts.append((blob_name, blob_text))
  return downloaded_texts

def fetch_blob_metadata(title: str) -> tuple[dict, bool]:
  
  container_client = blob_service_client.get_container_client(OUTPUT_CONTAINER_NAME)
  new_entry_flag = False
  
  try:
    blob = BlobClient.from_connection_string(conn_str=AZURE_CONNECTION_STRING, container_name=OUTPUT_CONTAINER_NAME, blob_name=title)
    if blob.exists():
      docs = [d for d in container_client.list_blobs(name_starts_with=title)]
      doc_metadata_tup = docs[0].items()
      
      doc_dict = {}
  
      for a,b in doc_metadata_tup:
        doc_dict.setdefault(a, []).append(b)
      
      res = {key: doc_dict[key] for key in doc_dict.keys()
            & {'name', 'container', 'last_modified'}}
      
      for k, v in res.items():
        res[k] = v[0]
      
      return res, new_entry_flag
    else:
      new_entry_flag = True
      return {}, new_entry_flag
  except:
    print ('Could not connect to Container')
  

def check_data_freshness (scraped_data: str, title: str) -> bool:
  
  # Existing blob storage datetime handling
  document_blob_data, new_entry_flag = fetch_blob_metadata(title)
  
  
  # Newly Scraped Datetime handling
  update_string = 'Last updated'
  before_update_string, update_string, after_update_string = scraped_data.partition(update_string)
  
  
  # 1st Case: If "Last updated" substring not found in webpage, and the new entry flag from fetching the blob is True, we can return True as we can consider this webpage needs to be "refreshed" a.k.a uploaded to blob
  
  # 2nd Case: If "Last updated" substring not found in webpage, we can return False as the webpage must have not been updated since first publishing.
  #           Given this case will only be reached if the new_entry_flag is False, we can assume at this point that we do not need to update the webpage.
  if not update_string and new_entry_flag:
    return True
  elif not update_string:
    return False
  
  scraped_date_str = after_update_string.split()[:3] # first 3 words
  scraped_date_str = " ".join(scraped_date_str)
  
  scraped_datetime = datetime.strptime(scraped_date_str, "%d %B %Y")
  scraped_datetime = scraped_datetime.astimezone(timezone('UTC'))
  

  if new_entry_flag:
    return True
  else:
    blob_last_modified_date = document_blob_data.get('last_modified')
    
    # Returns True if newly scraped webpage has been modified since the last blob refresh
    return scraped_datetime > blob_last_modified_date


def split_content_by_headings(doc_title: str, markdown_content: str) -> list[tuple[str, str]]:
  # Define the regular expression pattern to match H1 and H2 headings
  pattern = r'((?<!#)#{1,2}(?!#).*)'

  # Split the Markdown text based on the headings
  sections = re.split(pattern, markdown_content)
  
  
  url = sections[0].strip().replace('\n', '')
  sections = sections[1:]
  # Combine each heading with its corresponding text
  combined_sections = []
  for i in range(0, len(sections), 2):
    heading = sections[i].strip()  # Get the heading from sections[i]
    heading = heading.replace("#", "")
    output_content_chunk = sections[i + 1].strip() if i + 1 < len(
        sections) else ''  # Get the text from sections[i + 1] if it exists, otherwise use an empty string
      
    chunk_title = doc_title.replace(".txt", (" --" + str(heading) + ".txt"))
    doc_chunk_tup = (chunk_title, output_content_chunk)
    combined_sections.append(doc_chunk_tup)  # Add the combined section to the list

  return combined_sections, url
