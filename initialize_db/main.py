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

def get_enums(fieldname="analysis__host__host_gender"):
    
    json_query = "query{file{aggregations(include_missing:true){"+fieldname+"{buckets{key}}}}}"
    json_response = call_graphql_api(json_query)

    nested_enums = json_response["data"]["file"]["aggregations"][fieldname]["buckets"]

    enums_list = [
        single_enum["key"].replace('"', r'\"') 
        for single_enum in nested_enums
    ]

    return enums_list

def get_fieldinfos():
    json_query_all = 'query{__type(name: "fileAggregations") {fields {name type{name}}}}'
    json_response_all = call_graphql_api(json_query_all)
    fields = json_response_all['data']['__type']['fields']

    fieldsinfo = [
        {'fieldname': field['name'], 'fieldtype': field['type']['name']}
        for field in fields
    ]
    return fieldsinfo
