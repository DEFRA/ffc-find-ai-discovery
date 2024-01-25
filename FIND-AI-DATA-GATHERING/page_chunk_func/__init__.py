import logging

from azure.functions import InputStream
from .app_settings import *
from .helper_functions import *

def main(myblob: InputStream):
    logging.info(f"Python blob trigger function processed blob \n"
                 f"Name: {myblob.name}\n"
                 f"Blob Size: {myblob.length} bytes")
    
    blob_name = myblob.name
    blob_content = myblob.read().decode('utf-8')
    
    try:
        
        blob_chunked_tups, blob_url = split_content_by_headings(blob_name, blob_content)
        for chunk in blob_chunked_tups:
            if check_data_freshness(chunk[1], chunk[0]):
                blob_client = blob_service_client.get_blob_client(container = OUTPUT_CONTAINER_NAME,
                                                                    blob = chunk[0])
                
                logging.info("\nUploading Chunk to Azure Storage as blob:\n\t" + chunk[0])
                
                blob_title = blob_name.replace(".txt", "")
                
                blob_title = blob_title.encode('utf-8')
                
                section_file_name = chunk[0].split(' -- ')[1]
                section_title = section_file_name.replace('.txt', '') 
            
                blob_client.upload_blob(chunk[1], overwrite = True)
                blob_client.set_blob_metadata({'webpage_url': str(blob_url),
                                            'doc_title': str(blob_title),
                                            'section': str(section_title)})
            else:
                logging.info("\n"+ str(chunk[0]) + ' is already up-to-date.')
    except Exception as error:
        logging.warning(f"WARNING: FAILED TO CHUNK WEBPAGE: {blob_name}")
        logging.exception(error)
        

    