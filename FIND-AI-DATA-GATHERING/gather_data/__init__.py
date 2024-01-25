import logging

from azure.functions import TimerRequest
from datetime import datetime, timezone
from .app_settings import *
from .data_gathering_funcs import *
from azure.storage.blob import BlobServiceClient, ContainerClient



blob_service_client = BlobServiceClient.from_connection_string(CONTAINER_CONNECT_STRING)

def main(mytimer: TimerRequest) -> None:
    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone('UTC')).isoformat()
    
    
    
    if mytimer.past_due:
        logging.info('The timer is past due!')
        
    all_links = get_all_links_from_reference(base_url)
    for link in all_links:
        try:
            
            doc_title, webpage_content = create_documents_from_webpage(link)
            
            if check_data_freshness(webpage_content, doc_title):
                webpage_data = str(link) + "\n" + webpage_content
                webpage_data = webpage_data.encode('utf-8')
                webpage_file_name = str(doc_title) + ".txt"
                
                blob_client = blob_service_client.get_blob_client(container = CONTAINER_NAME_STRING,
                                                                    blob = webpage_file_name)
                
                logging.info("\nUploading to Azure Storage as blob:\n\t" + webpage_file_name)
                
                doc_title = doc_title.encode('utf-8')
                
                blob_client.upload_blob(webpage_data, overwrite = True)
                blob_client.set_blob_metadata({"webpage_url": str(link), "doc_title": str(doc_title)})
            else:
                logging.info("\n"+ str(doc_title) + ' is already up-to-date.')
        except Exception as error:
            logging.warning(f"WARNING: FAILED TO PROCESS WEBPAGE: {doc_title}")
            logging.exception(error)
    

    logging.info('Python timer trigger function ran at %s', utc_timestamp)