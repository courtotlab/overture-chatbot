import json
from operator import itemgetter
from langchain_community.utilities.graphql import GraphQLAPIWrapper
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def query_graphql(query):

    modified_query = query
    for sqon_keyword in ['fieldName', 'value', 'op', 'content']:
        modified_query = modified_query.replace(
            '"'+sqon_keyword+'"', sqon_keyword
        )

    graphql_query = f"{{file{{hits(filters:{modified_query}){{total}}}}}}"

    graphql = GraphQLAPIWrapper(
        graphql_endpoint="https://arranger.virusseq-dataportal.ca/graphql"
    )
    response = graphql.run(query=graphql_query)
    total = json.loads(response)['file']['hits']['total']

    return str(total)

def query_graphql_chain():

    llm = Ollama(model="mistral", temperature=0)

    json_prompt = """
    You are a structured output bot. Your task is to take a query and format it into the following JSON schema:

    {{"type": "object", "required": ["content", "op"], "properties": {{"content": {{"type": "array", "items": {{"oneOf": [{{"$ref": "#/$defs/FieldOperations"}}, {{"$ref": "#"}}]}}, "minItems": 1}}, "op": {{"default": "and", "enum": ["and", "or", "not"], "type": "string"}}}}, "$defs": {{"FieldOperations": {{"type": "object", "required": ["content", "op"], "properties": {{"content": {{"type": "array", "items": {{"oneOf": [{{"$ref": "#/$defs/Value01"}}, {{"$ref": "#/$defs/Value02"}}, {{"$ref": "#/$defs/Value03"}}]}}, "maxItems": 1, "minItems": 1}}, "op": {{"default": "in", "enum": ["in", "<=", ">="], "type": "string"}}}}}}, "Value01": {{"type": "object", "required": ["value"], "properties": {{"fieldName": {{"const": "analysis.host.host_gender", "type": "string", "description": "Gender of the individual who provided the sample."}}, "value": {{"type": "array", "items": {{"enum": ["Male", "Female", "Not Provided", "Restricted Access", "Unknown", "Missing", "Undeclared"], "type": "string"}}, "minItems": 1}}}}}}, "Value02": {{"type": "object", "required": ["value"], "properties": {{"fieldName": {{"const": "analysis.sample_collection.sample_collected_by", "type": "string", "description": "Name of institute that collected the sample"}}, "value": {{"type": "array", "items": {{"enum": ["Newfoundland and Labrador - Eastern Health", "Nova Scotia Health Authority"], "type": "string"}}, "minItems": 1}}}}}}, "Value03": {{"type": "object", "required": ["value"], "properties": {{"fieldName": {{"const": "analysis.first_published_at", "type": "string", "description": "Date first data was first published"}}, "value": {{"type": "integer"}}}}}}}}}}

    You must convert all dates in the first draft query to Unix timestamps UTC. 

    Make sure to check for common mistakes, including:
    - Respect the 'maxItems' and 'minItems' value
    - Only include the value if it is in the list following the "enum" keyward.

    You must response with the single line JSON object without explaination or notes.

    ###
    Here are some examples:

    Query: Filter for males in the database
    Response: {{'op': 'and', 'content': [{{'op': 'in', 'content': {{'fieldName': 'analysis.host.host_gender', 'value': ['Male']}}}}]}}
    Query: Get the number of samples who are not men
    Response: {{'op': 'not', 'content': [{{'op': 'in', 'content': {{'fieldName': 'analysis.host.host_gender', 'value': ['Male']}}}}]}}
    Query: Find the number of samples in Labrador not collected from men
    Response: {{'op': 'and', 'content': [{{'op': 'in', 'content': {{'fieldName': 'analysis.sample_collection.sample_collected_by', 'value': ['Newfoundland and Labrador - Eastern Health']}}}}, {{'op': 'not', 'content': [{{'op': 'in', 'content': {{'fieldName': 'analysis.host.host_gender', 'value': ['Male']}}}}]}}]}}
    Query: Get all samples published after 1640926800000
    Response: {{"op": "and", "content": [{{"op": ">=", "content": {{"fieldName": "analysis.first_published_at", "value": 1640926800000}}}}]}}
    ###

    <<<
    Query: {query}
    >>>
    """

    prompt = PromptTemplate(
        template=json_prompt,
        input_variables=["query"]
    )

    answer_prompt_template = """
        Given the following user question, corresponding query, and result, print the Query Result on the first line and answer the user question on the second line.
                                                 
        ###
        Here is an example:
        Question: Find the number of males in Nova Scotia
        JSON query schema: {{"op": "and", "content": [{{"op": "in", "content": {{"fieldName": "analysis.host.host_gender", "value": ["Male"]}}}}, {{"op": "in", "content": {{"fieldName": "analysis.sample_collection.sample_collected_by", "value": ["Nova Scotia Health Authority"]}}}}]}}
        Query result: 3379
        Answer: There are 3779 males in Nova Scotia.                                     
        ###

        Question: {query}
        Query: {query_schema}
        Query Result: {result}
        Answer: 
    """
    answer_prompt = PromptTemplate(template=answer_prompt_template)

    query_schema_chain = prompt | llm
    answer_chain = (
        RunnablePassthrough.assign(query_schema=query_schema_chain).assign(
            result=itemgetter("query_schema") | RunnableLambda(query_graphql)
        )
        | answer_prompt
        | llm
        | StrOutputParser()
    )

    return answer_chain

def get_keyword_chain():

    llm = Ollama(model="mistral", temperature=0)

    keyword_prompt = """
        You are expert English linguist. Extract all the keywords from the given database query.

        Constraints: Limit the number of keywords to a maximum of five. Only include the list of keywords.

        ###
        Here are some examples:

        Query: Get the number of samples who are not men
        Response: men
        Query: Find the number of samples in Labrador not collected from men
        Response: Labrador, men
        Query: Get all samples published after 1640926800000
        Response: 1640926800000
        ###

        <<<
        Query: {query}
        >>>
    """

    prompt = PromptTemplate(
        template=keyword_prompt,
        input_variables=['query']
    )
    chain = prompt | llm

    return chain

def get_sqon_keyword(keyword_str):
    """Get filtering SQONs (as JSON) from a string of keywords

    Parameters
    ----------
    keyword_str : str
        String containing keywords separated by a comma (e.g. 'man, woman')

    Returns
    -------
    list[str]
        List containing strings of filtering SQONs related to keywords
    """
    embeddings = HuggingFaceEmbeddings(
        model_name='multi-qa-mpnet-base-cos-v1',
        cache_folder='../resources/huggingface'
    )

    # vector database containing the filtering SQONs
    vector_store = Chroma(
        collection_name="overture",
        embedding_function=embeddings,
        persist_directory='../resources/chroma'
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    # separate string into individual keywords
    keyword_lst = keyword_str.split(', ')

    sqons = []
    for kwrd in keyword_lst:
        documents = retriever.invoke(kwrd.strip())
        sqons.extend([doc.metadata['schema'] for doc in documents])

    sqons = list(set(sqons))

    return sqons

def format_sqons_schema(sqons):

    json_refs_open = (
        '{{"type": "object", "required": ["content", "op"], "properties": {{"content": '
        '{{"type": "array", "items": {{"oneOf": [{{"$ref": "#/$defs/FieldOperations"}}, '
        '{{"$ref": "#"}}]}}, "minItems": 1}}, "op": {{"default": "and", '
        '"enum": ["and", "or", "not"], "type": "string"}}}}, "$defs": '
        '{{"FieldOperations": {{"type": "object", "required": ["content", "op"], '
        '"properties": {{"content": {{"type": "array", "items": {{"oneOf": ['
    )
    json_refs_close = (
        ']}}, "maxItems": 1, "minItems": 1}}, "op": {{"default": "in", '
        '"enum": ["in", "<=", ">="], "type": "string"}}}}}}, '
    )
    schema_close = '}}}}}'

    json_refs = ''
    json_defs = ''
    # https://json-schema.org/understanding-json-schema/structuring
    for i in range(len(sqons)):
        json_refs = json_refs + """{{"$ref": "#/$defs/Value""" + str(i) + """"}}"""
        json_defs = json_defs + """"Value""" + str(i) + '": ' + sqons[i]
        if i != (len(sqons)-1):
            json_refs = json_refs + ', '
            json_defs = json_defs + ', '

    sqon_json = json_refs_open + json_refs + json_refs_close + json_defs + schema_close

    return sqon_json
