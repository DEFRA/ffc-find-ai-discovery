import logging
import datetime
import json

from azure.functions import HttpRequest, HttpResponse
from app_settings import *
from helper_functions import *

def main(req: HttpRequest) -> HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    values = req.params.get('values')
    if not values:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            values = req_body.get('values') 
            
    try:   
        data = values[0]['data']
        record_id = values[0]["recordId"]
        document_id = data["document_id"]
        
        text = data["text"]
        filename = data["filename"]
        
        logging.info(filename)
        logging.info(document_id)
        
        doc_chunks, doc_url = split_content_by_headings(str(filename), str(text))
        
        blob_title = filename.replace(".txt'", "")
        blob_title = blob_title.replace((INPUT_CONTAINER_NAME + "/"), "")
        
        
        current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        chunks_list = []
        
        for idx, chunk in enumerate(doc_chunks):
            
            section_file_name = chunk[0].split(' -- ')[1]
            chunk_title = section_file_name.replace('.txt', '') 
        
            chunk_identifier = f"(Title: {blob_title} | Source: {doc_url} | Section: {chunk_title})==="
        
            output_content = chunk_identifier + chunk[1]
            
            chunkJson = {
                "content": output_content,
                "chunk_id": str(idx),
                "title": chunk[0],
                "filepath": filename,
                "source_url": doc_url,
                "last_updated": current_datetime
            }
            
            chunks_list.append(chunkJson)
            
        
        response = {"values": [
            {
                "recordId": record_id,
                "data": {
                    "chunks": chunks_list,
                    "total_files": len(chunks_list),
                    "num_unsupported_format_files": 0,
                    "num_files_with_errors": 0,
                    "skipped_chunks": 0
                },
                "errors": None,
                "warnings": None
            }
        ]
        }
        
        return HttpResponse(
            json.dumps(response),
            mimetype="application/json"
        )
    except Exception as error:
        return HttpResponse(error)