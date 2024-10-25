"""Initialize vector database

This script is intended to be run once initially to initialize the vector database, 
save the vector database locally, and download the associated embeddings (from HuggingFace).
"""

import json
import requests
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def main():

    # store information to put into vector database
    documents =[]

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
            documents.append(Document(page_content=description, metadata=schema))
            if enums_list:
                documents.append(Document(page_content=repr(enums_list), metadata=schema))

    embeddings = HuggingFaceEmbeddings(
        model_name='multi-qa-mpnet-base-cos-v1',
        cache_folder='../resources/huggingface'
    )

    # create connection to vector database
    vector_store = Chroma(
        collection_name='overture',
        embedding_function=embeddings,
        persist_directory='../resources/chroma'
    )

    # add data to database
    vector_store.add_documents(
        documents=documents,
        ids=["id"+str(i) for i in range(len(documents))]
    )

def create_value_object_schema(
    fieldname, fieldtype, description = None
):
    """Create SQON value object and description of field name

    Parameters
    ----------
    fieldname : str
        Name of field of interest.
    fieldtype : str
        Data type (Aggregations or NumericalAggregations) of fieldname.
    description : str, optional
        Short description of the field associated with fieldname, by default None.

    Returns
    -------
    value_object : str
        JSON representation of a SQON value object.
    description : str
        Short description of the field associated with fieldname. If no description 
        is initially provided, the file name will be parsed and used as the description.
    enums_list : list of str
        List of enumerations assoicated with filename.
    """

    if fieldtype == "Aggregations":
        enums_list = get_enums(fieldname)
        mod_enums_list = repr(enums_list).replace("'", '"')

        properties_value = (
            '"value": {'
                '"type": "array", '
                '"items": {'
                    f'"enum": {mod_enums_list}, '
                    '"type": "string"'
                '}, '
                '"minItems": 1'
            '}'
        )

    elif fieldtype == "NumericalAggregations":
        enums_list = []

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

    return value_object, description, enums_list

def get_enums(fieldname="analysis__host__host_gender"):
    """Get the enumerated data from a field using GraphQL

    Parameters
    ----------
    fieldname : str
        Field that we wish to obtain enums for.

    Returns
    -------
    list
        Each item of list represents the enumerated data for the given field.
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
        Each item in the list is a dictionary with a 'fieldname' and 'fieldtype' keys.
    """
    json_query_all = 'query{__type(name: "fileAggregations") {fields {name type{name}}}}'
    json_response_all = call_graphql_api(json_query_all)
    fields = json_response_all['data']['__type']['fields']

    fieldsinfo = [
        {'fieldname': field['name'], 'fieldtype': field['type']['name']}
        for field in fields
    ]
    return fieldsinfo

def call_graphql_api(
    # TODO: abstract this value into an EnvVar
    json_query, url='https://arranger.virusseq-dataportal.ca/graphql'
):
    """Create a GraphQL call and return the result

    Parameters
    ----------
    json_query : str
        GraphQL query in JSON.
    url : str
        URL where the GraphQL query is sent.

    Returns
    -------
    str
        GraphQL response in a JSON string.
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

if __name__ == '__main__':
    main()
