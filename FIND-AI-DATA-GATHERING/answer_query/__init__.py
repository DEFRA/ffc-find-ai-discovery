import logging
import json
from azure.functions import HttpRequest, HttpResponse
from .helper_funcs import *
from .app_settings import *

def main(req: HttpRequest) -> HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    input = req.params.get('input')
    if not input:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            input = req_body.get('input')
            
    logging.info(f'Processing user query: {input}')
    
    response = answer_query(input)
    test_url = 'https://www.gov.uk/government/publications/slurry-infrastructure-grant-round-2-applicant-guidance/item-specification-and-grant-contribution'
    response_dict = {'answer': response, 'source_urls': [test_url]}
    
    response_json = json.dumps(response_dict)
    return HttpResponse(response_json,
                        mimetype="application/json")