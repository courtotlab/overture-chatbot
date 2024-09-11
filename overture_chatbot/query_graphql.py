import json
from langchain_community.utilities.graphql import GraphQLAPIWrapper
from langchain_core.prompts import PromptTemplate
from langchain_community.llms import Ollama

def query_graphql(input):

    modified_input = input
    for sqon_keyword in ['fieldName', 'value', 'op', 'content']:
        modified_input = modified_input.replace(
            '"'+sqon_keyword+'"', sqon_keyword
        )

    graphql_query = f"{{file{{hits(filters:{modified_input}){{total}}}}}}"

    graphql = GraphQLAPIWrapper(
        graphql_endpoint="https://arranger.virusseq-dataportal.ca/graphql"
    )
    response = graphql.run(query=graphql_query)
    total = json.loads(response)['file']['hits']['total']

    return str(total)

def query_graphql_chain():

    llm = Ollama(model="mistral", temperature=0)

    json_prompt = """
    You are a structed output bot. Your task is to take a query and format it into the following JSON schema:

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

    chain = prompt | llm | query_graphql

    return chain
