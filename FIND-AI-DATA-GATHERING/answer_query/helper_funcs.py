import openai
import tiktoken

from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from .app_settings import *

azure_ai_search_credential = AzureKeyCredential(key)

search_client = SearchClient(endpoint=service_endpoint,
                      index_name=index_name,
                      credential=azure_ai_search_credential)

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



def create_filter_expression(selected_schemes: list):
    scheme_tags = ['Countryside Stewardship (CS)',
                   'Sustainable Farming Incentive (SFI)',
                   'Slurry Infrastructure Grant (SIG)',
                   'Farming Equipment and Technology Fund (FETF)']
    
    filter_field = 'grant_scheme_name'
    
    if selected_schemes:
        schemes_for_expression = []
        for item in selected_schemes:
            if item == "CS":
                schemes_for_expression.append(scheme_tags[0])
            elif item == "FETF":
                schemes_for_expression.append(scheme_tags[3])
            elif item == "SIG":
                schemes_for_expression.append(scheme_tags[2])
            elif item == "SFI":
                schemes_for_expression.append(scheme_tags[1])
        
        filter_sub_expressions = []
        for item in schemes_for_expression:
            filter_sub_expr = f"{filter_field} eq '{item}'"
            filter_sub_expressions.append(filter_sub_expr)
        
        return 'or'.join(filter_sub_expressions)
    else:
        return ""

def single_vector_search(user_query: str, selected_schemes: list):
    # [START single_vector_search]
    vector_query = VectorizedQuery(vector=embed_query(user_query), k_nearest_neighbors=20, fields="vector")
    filter_string = create_filter_expression(selected_schemes)
    results = search_client.search(
        vector_queries=[vector_query],
        filter=filter_string,
        select=["chunk"]
    )
    
    return results



def query_message(
    query: str,
    token_budget: int,
    selected_schemes: list = []
) -> str:
    """Return a message for GPT, with relevant source texts pulled from Azure AI index."""
    strings = single_vector_search(query, selected_schemes)
    
    question = f"\n\nQuestion: {query}"
    #message = model_custom_intro
    message = ""
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
    token_budget: int = 16384 - 1024,
    print_message: bool = False,
    selected_schemes: list = []
) -> str:
    """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
    message = query_message(query, token_budget = token_budget, selected_schemes = selected_schemes)
    if print_message:
        print(message)
    messages = [
        {"role": "system", "content": model_custom_intro},
        {"role": "user", "content": message},
    ]
    response = openai_client.chat.completions.create(
        model=gpt_model,
        messages=messages,
        temperature=0.0,
        stream=False
    )
    
    return response.choices[0].message.content