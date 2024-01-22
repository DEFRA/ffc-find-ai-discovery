import requests
from bs4 import BeautifulSoup as bs
from datetime import datetime
from pytz import timezone
import re
from html2text import html2text
from azure.storage.blob import BlobServiceClient, BlobClient
from .app_settings import *

blob_service_client = BlobServiceClient.from_connection_string(CONTAINER_CONNECT_STRING)

base_url = 'https://www.gov.uk/countryside-stewardship-grants'
cs_overview_url = 'https://www.gov.uk/guidance/countryside-stewardship-get-funding-to-protect-and-improve-the-land-you-manage'
site_visits_url = 'https://www.gov.uk/guidance/site-visits-countryside-stewardship-and-environmental-stewardship'
gov_uk_prefix = 'https://www.gov.uk'


def get_links_from_page(base_url: str, index: int) -> list:
  req = requests.get(base_url + "?page=" + str(index))
  soup = bs(req.text, 'html.parser')
  base_url_data = soup.find_all('div',attrs = {'class','gem-c-document-list__item-title'})
  grant_links = []
  for div in base_url_data:
    links = div.findAll('a')
    for a in links:
      grant_links.append(a['href'])
  return grant_links


def get_all_links_from_reference(base_url: str) -> list:
  all_grant_urls = []
  for index in range(1, 7):
    all_grant_urls.extend(get_links_from_page(base_url, index))

  all_grant_urls = [gov_uk_prefix + href for href in all_grant_urls]
  all_grant_urls.extend([cs_overview_url, site_visits_url])
  return all_grant_urls


def scrape_webpage(url: str) -> bs:
  req = requests.get(url)
  soup = bs(req.text, 'html.parser')
  return soup


def webpage_to_markdown(soup: bs) -> str:
  # Find main content div from webpage
  main_div = soup.find("div", {"class": "app-c-contents-list-with-body"})
  # Extract the HTML content from the text body
  html_content = str(main_div)

  # Convert the HTML content into markdown for easier processing
  markdown_content = html2text(html_content, bodywidth=0)
  return markdown_content


def strip_links_from_markdown(markdown_content: str) -> str:
  # Make a RegEx pattern
  link_pattern = re.compile(r'\[(.*?)\]\((.*?)\)')

  # Find all matches in markdown_content
  matches = link_pattern.findall(markdown_content)

  for _match in matches:
    full_match = f'[{_match[0]}]({_match[1]})'

    # Replace the full link with just the text
    markdown_content = markdown_content.replace(full_match, _match[0])

  return markdown_content


def create_documents_from_webpage(url: str) -> tuple[str, str]:
  soup = scrape_webpage(url)
  # Extract the title from the article
  title = soup.find('h1',{"class": "gem-c-title__text govuk-heading-l"}).get_text().strip()
  title = title.replace("\\", "")
  title = title.replace("/", "or")

  # Convert the webpage HTML to markdown
  markdown_content = webpage_to_markdown(soup)
  stripped_content = strip_links_from_markdown(markdown_content)
  
  heading_pattern = r'(#{1,2}[\r\n\s0-9\.a-z\'\-\’A-Z\(\)]*)'
  split_by_heading = re.split(heading_pattern, stripped_content, maxsplit=1)[2]
  
  update_pattern = r'^[\r\na-zA-z0-9\(\)\s#\S]*(Last[\s]{1}updated[\s]{1}[0-9]{1,2} [a-zA-z]+ [0-9]{4})'
  update_string_flag = re.search(update_pattern, split_by_heading)
  
  if update_string_flag:
    cleaned_content = update_string_flag.group(0)
  else:
    update_pattern = r'^[\r\na-zA-z0-9\(\)\s#\S]*(Published[\s]{1}[0-9]{1,2} [a-zA-z]+ [0-9]{4})'
    update_string_flag = re.search(update_pattern, split_by_heading)
    if update_string_flag:
      cleaned_content = update_string_flag.group(0)
    else:
      cleaned_content = split_by_heading
  
  return title, cleaned_content


def fetch_blob_data(title: str) -> tuple[dict, bool]:
  
  container_client = blob_service_client.get_container_client(CONTAINER_NAME_STRING)
  new_entry_flag = False
  
  try:
    blob_title = str(title) + '.txt'
    blob = BlobClient.from_connection_string(conn_str=CONTAINER_CONNECT_STRING, container_name=CONTAINER_NAME_STRING, blob_name=blob_title)
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
  document_blob_data, new_entry_flag = fetch_blob_data(title)
  
  
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


