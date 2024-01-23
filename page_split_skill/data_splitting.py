import re
import logging
from azure.storage.blob import BlobServiceClient, BlobClient
from .app_settings import *
from .helper_functions import *


blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)


def write_chunk_blobs():
    blob_plaintext_list = download_blobs_to_string(blob_service_client, INPUT_CONTAINER_NAME)
    
    for blob in blob_plaintext_list:
        blob_chunked_tups = split_markdown_by_headings(blob[0], blob[1])
        for chunk in blob_chunked_tups:
            
            blob_client = blob_service_client.get_blob_client(container = OUTPUT_CONTAINER_NAME,
                                                                blob = chunk[0])

            logging.info("\nUploading Chunk to Azure Storage as blob:\n\t" + chunk[0])

            blob_client.upload_blob(chunk[1], overwrite = True)


write_chunk_blobs()