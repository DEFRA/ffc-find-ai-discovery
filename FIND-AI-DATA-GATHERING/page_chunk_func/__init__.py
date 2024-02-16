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
        
        #blob_chunked_tups, blob_url = split_content_by_headings(blob_name, blob_content)
        blob_url, grant_scheme_name, stripped_content = get_source_metadata(blob_content)
        
        logging.info(stripped_content)
        
        blob_chunks = chunk_tokens(stripped_content)
        
        blob_raw_title = blob_name.replace(".txt", "")
        blob_title = blob_raw_title.replace((INPUT_CONTAINER_NAME + "/"), "")
        
        for i, text in enumerate(blob_chunks):
            identifier = f"(Title: {blob_title} | Source: {blob_url} | Chunk Number: {str(i)})==="
            chunk_content = identifier + text
            
            chunk_title = f"{blob_raw_title}_{i}.txt"
            
            blob_client = blob_service_client.get_blob_client(container = OUTPUT_CONTAINER_NAME,
                                                                    blob = chunk_title)
                
            logging.info("\nUploading Chunk to Azure Storage as blob:\n\t" + chunk_title)
            
            blob_client.upload_blob(chunk_content, overwrite=True)
            blob_client.set_blob_metadata({'source_url': blob_url, 'document_title': blob_title, 'grant_scheme_name': grant_scheme_name})
            
        #for chunk in blob_chunked_tups:
        #    if check_data_freshness(chunk[1], chunk[0]):
#
#                blob_client = blob_service_client.get_blob_client(container = OUTPUT_CONTAINER_NAME,
#                                                                    blob = chunk[0])
#                
#                logging.info("\nUploading Chunk to Azure Storage as blob:\n\t" + chunk[0])
#
#                blob_title = blob_name.replace(".txt", "")
#                blob_title = blob_title.replace((INPUT_CONTAINER_NAME + "/"), "")
#                
#                                
#                section_file_name = chunk[0].split(' -- ')[1]
#                section_title = section_file_name.replace('.txt', '') 
#                
#                identifier = f"(Title: {blob_title} | Source: {blob_url} | Section: {section_title})==="
#                
#                chunk_content = identifier + chunk[1]                
#                
#                
#                blob_client.upload_blob(chunk_content, overwrite = True)
#               
    except Exception as error:
        logging.warning(f"WARNING: FAILED TO CHUNK WEBPAGE: {blob_name}")
        logging.exception(error)
        

    