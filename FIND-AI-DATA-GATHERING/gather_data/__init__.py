import logging

from azure.functions import TimerRequest
from datetime import datetime, timezone
from .app_settings import *
from .data_gathering_funcs import *
from azure.storage.blob import BlobServiceClient



blob_service_client = BlobServiceClient.from_connection_string(CONTAINER_CONNECT_STRING)

def main(mytimer: TimerRequest) -> None:
    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone('UTC')).isoformat()
    
    
    
    if mytimer.past_due:
        logging.info('The timer is past due!')
        
        all_links = get_all_links_from_reference(base_url)
        for link in all_links:
            doc_title, webpage_content = create_documents_from_webpage(link)
            
            if check_data_freshness(webpage_content, doc_title):
                webpage_data = str(link) + "\n" + webpage_content
                webpage_data = webpage_data.encode('utf-8')
                webpage_file_name = str(doc_title) + ".txt"
                
                blob_client = blob_service_client.get_blob_client(container = CONTAINER_NAME_STRING,
                                                                    blob = webpage_file_name)
                
                print("\nUploading to Azure Storage as blob:\n\t" + webpage_file_name)
                
                blob_client.upload_blob(webpage_data, overwrite = True)
            else:
                print ("\n"+ str(doc_title) + ' is already up-to-date.')
    else:
        logging.info('Code did not run as timer is not past due')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)
