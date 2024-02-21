import openai
import tiktoken

from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from app_settings import *

search_client = SearchClient(endpoint=service_endpoint,
                      index_name=index_name,
                      credential=key)

openai_client = openai.AzureOpenAI(
        azure_endpoint=open_ai_endpoint,
        api_key=open_ai_key,
        api_version="2023-12-01-preview",
    )



def embed_query(text: str):
    embedding = openai_client.embeddings.create(input=[text], model="text-embedding-ada-002")
    return embedding.data[0].embedding



def num_tokens(text: str, model: str = gpt_model) -> int:
    """Return the number of tokens in a string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))



def single_vector_search(user_query: str):
    # [START single_vector_search]
    vector_query = VectorizedQuery(vector=embed_query(user_query), k_nearest_neighbors=3, fields="contentVector")

    results = search_client.search(
        vector_queries=[vector_query],
        select=["content"]
    )
    
    return results



def query_message(
    query: str,
    token_budget: int
) -> str:
    """Return a message for GPT, with relevant source texts pulled from Azure AI index."""
    strings = single_vector_search(query)
    
    question = f"\n\nQuestion: {query}"
    message = model_custom_intro
    for string in strings:
        next_article = f'\n\nDEFRA Farming Grant Options Document:\n"""\n{string}\n"""'
        if (
            num_tokens(message + next_article + question, model=gpt_model)
            > token_budget
        ):
            break
        else:
            message += next_article
    return message + question


def answer_query(
    query: str,
    token_budget: int = 16384 - 500,
    print_message: bool = False,
) -> str:
    """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
    message = query_message(query, token_budget=token_budget)
    if print_message:
        print(message)
    messages = [
        {"role": "system", "content": "You answer questions about the DEFRA Countryside Stewardship grant program."},
        {"role": "user", "content": message},
    ]
    response = openai_client.completions.create(
        model=gpt_model,
        messages=messages,
        temperature=0.0,
        stream=False
    )
    response_message = response.choices[0].message.content
    return response_message