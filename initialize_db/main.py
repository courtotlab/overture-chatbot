import json
import requests

def call_graphql_api(
        json_query, url='https://arranger.virusseq-dataportal.ca/graphql'
):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Connection': 'keep-alive',
        'DNT': '1'
    }
    json_data = {'query': json_query}
    response = requests.post(
        url=url, headers=headers, json=json_data, timeout=300
    )
    response_json = json.loads(response.content)

    return response_json
