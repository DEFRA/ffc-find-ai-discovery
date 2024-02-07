import logging
import json

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
        chunk_num = 0
        for chunk in blob_chunked_tups:
            if check_data_freshness(chunk[1], chunk[0]):
                
                blob_out_name = chunk[0].replace(".txt", ".json")

                blob_client = blob_service_client.get_blob_client(container = OUTPUT_CONTAINER_NAME,
                                                                    blob = blob_out_name)
                
                logging.info("\nUploading Chunk to Azure Storage as blob:\n\t" + chunk[0])
                
                blob_title = blob_name.replace(".txt'", "")
                blob_title = blob_title.replace((INPUT_CONTAINER_NAME + "/"), "")
                
                                
                section_file_name = chunk[0].split(' -- ')[1]
                section_title = section_file_name.replace('.txt', '') 
                
                output_dict = {'chunk_id': chunk_num , 'content': chunk[1],'doc_title': blob_title ,'chunk_title': section_title, 'source_url': blob_url}
                output_json = json.dumps(output_dict)
                blob_client.upload_blob(output_json, overwrite = True)
                chunk_num += 1
                
            else:
                logging.info("\n"+ str(chunk[0]) + ' is already up-to-date.')
    except Exception as error:
        logging.warning(f"WARNING: FAILED TO CHUNK WEBPAGE: {blob_name}")
        logging.exception(error)
        

    