import json
import requests
import chromadb

def call_graphql_api(
    json_query, url='https://arranger.virusseq-dataportal.ca/graphql'
):
    """Create a GraphQL call and return the result

    Parameters
    ----------
    json_query : str
        GraphQL query in JSON
    url : str
        URL where the GraphQL query is sent

    Returns
    -------
    str
        GraphQL response in a JSON string
    """
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
    """Get the enumerated data from a field using GraphQL

    Parameters
    ----------
    fieldname : str
        Field that we wish to obtain enums for

    Returns
    -------
    list
        Each item of list represents the enumerated data for the given field
    """
    json_query = "query{file{aggregations(include_missing:true){"+fieldname+"{buckets{key}}}}}"
    json_response = call_graphql_api(json_query)

    nested_enums = json_response["data"]["file"]["aggregations"][fieldname]["buckets"]

    enums_list = [
        single_enum["key"].replace('"', r'\"')
        for single_enum in nested_enums
    ]

    return enums_list

def get_fieldinfos():
    """Get field information (i.e. field type) of project using GraphQL

    Returns
    -------
    list of dicts
        Each item in the list is a dictionary with a 'fieldname' and 'fieldtype' keys
    """
    json_query_all = 'query{__type(name: "fileAggregations") {fields {name type{name}}}}'
    json_response_all = call_graphql_api(json_query_all)
    fields = json_response_all['data']['__type']['fields']

    fieldsinfo = [
        {'fieldname': field['name'], 'fieldtype': field['type']['name']}
        for field in fields
    ]
    return fieldsinfo

def create_value_object_schema(
    fieldname = "", fieldtype = "", description = None
):

    if fieldtype == "Aggregations":
        enums_list0 = get_enums(fieldname)
        enums_list = repr(enums_list0).replace("'", '"')

        properties_value = (
            '"value": {'
                '"type": "array", '
                '"items": {'
                    f'"enum": {enums_list}, '
                    '"type": "string"'
                '}, '
                '"minItems": 1'
            '}'
        )

    elif fieldtype == "NumericalAggregations":
        properties_value = (
            '"value": {'
                '"type": "integer"'
            '}'
        )

    fieldname_periods = fieldname.replace("__", ".")

    if description is None:
        description = fieldname
        for r in ("__", "_"):
            description = description.replace(r, " ")

    properties_fieldname = (
        '"fieldName": {'
            f'"const": "{fieldname_periods}", '
            '"type": "string", '
            f'"description": "{description}"'
        '}'
    )

    value_object = (
        '{'
            '"type": "object", '
            '"required": ["value"], '
            '"properties": {'
                f'{properties_fieldname}, '
                f'{properties_value}'
            '}'
        '}'
    )

    return value_object, description, enums_list0

def main():

    # documents acts like a 'key' in the vector database
    documents =[]
    # metadata acts like a 'value' in the vector database
    metadatas = []

    fieldinfos = get_fieldinfos()

    for fieldinfo in fieldinfos:
        fieldname = fieldinfo['fieldname']
        fieldtype = fieldinfo['fieldtype']

        json_query = "query{file{aggregations(include_missing:true){"+fieldname+"{buckets{key}}}}}"
        json_response = call_graphql_api(json_query)

        if 'errors' not in json_response:
            value_object_schema, description, enums_list = create_value_object_schema(
                fieldname=fieldname,fieldtype=fieldtype
            )

            schema = {"schema": value_object_schema}

            documents.append(description)
            metadatas.append(schema)

            documents.append(repr(enums_list))
            metadatas.append(schema)

    chroma_client = chromadb.PersistentClient(path='../resources/chroma')

    # switch `create_collection` to `get_or_create_collection`
    # to avoid creating a new collection every time
    collection = chroma_client.get_or_create_collection(name="my_collection")

    # switch `add` to `upsert` to avoid adding the same documents every time
    collection.upsert(
        documents=documents,
        metadatas=metadatas,
        ids=["id"+str(i) for i in range(len(documents))]
    )
