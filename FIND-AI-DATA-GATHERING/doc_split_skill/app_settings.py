import os

AZURE_CONNECTION_STRING = os.getenv('GATHER_CONTAINER_CONNECTION_STRING')
INPUT_CONTAINER_NAME = os.getenv('GATHER_CONTAINER_NAME')
OUTPUT_CONTAINER_NAME = os.getenv('FIND_CHUNKS_CONTAINER_NAME')

open_ai_endpoint = os.getenv("OpenAIEndpoint")
open_ai_key = os.getenv("OpenAIKey")
embedding_model = "text-embedding-ada-002"