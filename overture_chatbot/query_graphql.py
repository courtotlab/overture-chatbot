"""Querying GraphQL API with LLMs

Functions associated with querying GraphQL APIs with LLMs.
Module is intended to be imported by a GUI.  
"""

import json
from operator import itemgetter
import chromadb
from chromadb.config import Settings
from langchain_community.utilities.graphql import GraphQLAPIWrapper
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.runnables import RunnableSequence, Runnable, RunnableConfig
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.tools import tool

llm = OllamaLLM(base_url='http://ollama-llm:11434', model='mistral', temperature=0)
embeddings = HuggingFaceEmbeddings(
    model_name='multi-qa-mpnet-base-cos-v1',
    cache_folder='resources/huggingface'
)

# vector database containing the filtering SQONs
chroma_client = chromadb.HttpClient(
        host='chroma-db', port=8000, settings=Settings(allow_reset=True, anonymized_telemetry=False)
    )
vector_store = Chroma(
    collection_name="overture",
    embedding_function=embeddings,
    client=chroma_client
)

def query_total_chain() ->  RunnableSequence:
    """Create a Langchain LCEL chain that returns the total number of records from unstructured text

    Returns
    -------
    langchain_core.runnables.base.RunnableSequence
        Langchain chain that will return total number of records from unstructured text.

    Notes
    -----
    The difference between query_total_chain() and query_total_summary_chain() is that 
    query_total_chain() returns only the number (i.e. 5) and query_total_summary_chain()
    returns the number as a summary (i.e. There are 5 records that match your criteria 
    of X, Y, and Z).
    """
    
    def try_except_total_graphql(args: str, config: RunnableConfig) -> Runnable:
        """Try/except for get_total_graphql

        Reference
        ---------
        https://python.langchain.com/docs/how_to/tools_error/#tryexcept-tool-call
        """
        sqon = args[1:]
        try:
            return get_total_graphql.invoke(sqon, config=config)
        except Exception as e:
            return f"Calling tool with arguments:\n\n{sqon}\n\nraised the following error:\n\n{type(e)}: {e}"
    
    query_total = create_sqon_schema() | format_sqon_filters | try_except_total_graphql

    return query_total

def query_total_summary_chain() -> RunnableSequence:
    """Create a Langchain LCEL chain that summarizes total number of records from unstructured text

    Returns
    -------
    langchain_core.runnables.base.RunnableSequence
        Langchain chain that summarizes the total number of records from unstructured text.

    Notes
    -----
    The difference between query_total_chain() and query_total_summary_chain() is that 
    query_total_chain() returns only the number (i.e. 5) and query_total_summary_chain()
    returns the number as a summary (i.e. There are 5 records that match your criteria 
    of X, Y, and Z).
    """
    def summarize_answer() -> RunnableSequence:
        """Create a Langchain LCEL chain that summarizes answer

        Chain will create a summary of the results given the query, query schema, and result.

        Returns
        -------
        langchain_core.runnables.base.RunnableSequence
            Langchain chain that summarizes the total number of records from unstructured text.

        See Also
        --------
        query_total_summary_chain
        """
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

        answer_chain = answer_prompt | llm

        return answer_chain

    query_schema_chain = create_sqon_schema() | format_sqon_filters

    answer_chain = (
        RunnablePassthrough.assign(query_schema=query_schema_chain).assign(
            result=itemgetter("query_schema") | RunnableLambda(get_total_graphql)
        )
        | summarize_answer()
        | StrOutputParser()
    )

    return answer_chain

def create_sqon_schema() -> RunnableSequence:
    """Create a Langchain LCEL chain that creates SQON prompt from unstructured text

    Returns
    -------
    langchain_core.runnables.base.RunnableSequence
        Langchain chain that creates SQON prompt from unstructured text.

    See Also
    --------
    query_total_summary_chain
    query_total_chain
    """
    sqon_prompt_template = """
        You are a structured output bot. Your task is to take a query and format it into the following JSON schema:

        {schema}

        Make sure to check for common mistakes, including:
        - Respect the 'maxItems' and 'minItems' value
        - Only include the value if it is in the list following the "enum" keyward.
        - The number of open brackets should equal the number of close brackets

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

    sqon_prompt = PromptTemplate(
        template=sqon_prompt_template,
        input_variables=["schema", "query"]
    )

    sqon_schema_chain = get_keyword_chain() | get_sqon_keyword | format_sqons_schema

    sqon_chain = (
        {
            "schema": sqon_schema_chain,
            "query": RunnablePassthrough()
        }
        | sqon_prompt
        | llm
    )

    return sqon_chain

def get_keyword_chain() -> RunnableSequence:
    """Create a Langchain LCEL chain that returns keywords extracted from unstructured text

    Returns
    -------
    langchain_core.runnables.base.RunnableSequence
        Langchain chain that will keywords extracted from unstructured text.
    """
    keyword_prompt_template = """
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
        template=keyword_prompt_template,
        input_variables=['query']
    )
    chain = prompt | llm

    return chain

def get_sqon_keyword(keyword_str: str) -> list[str]:
    """Get SQONs (as JSON) from a keyword

    Given a keyword, this function will query a vector store to retrieve 
    and return the related SQONs.

    Parameters
    ----------
    keyword_str : str
        String containing keywords separated by a comma (e.g. 'man, woman').

    Returns
    -------
    list of str
        List containing strings of filtering SQONs related to keywords.

    See Also
    --------
    initialize_db.main.main: Function to initialize vector store.
    """
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    # separate string into individual keywords
    keyword_lst = keyword_str.split(', ')

    sqons = []
    for kwrd in keyword_lst:
        documents = retriever.invoke(kwrd.strip())
        sqons.extend([doc.metadata['schema'] for doc in documents])

    sqons = list(set(sqons))

    return sqons

def format_sqons_schema(sqons: list[str]) -> str:
    """Integrate SQONs into JSON schema

    Parameters
    ----------
    sqons : list of str
        SQONs to be incorporated into JSON schema.

    Returns
    -------
    str
        JSON schema (represented by a string) for SQONs.

    Notes
    -----
    More information about JSON schemas can be found at 
    https://json-schema.org/understanding-json-schema/structuring.
    """
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
    for count, value in enumerate(sqons):
        json_refs = json_refs + """{{"$ref": "#/$defs/Value""" + str(count) + """"}}"""
        json_defs = json_defs + """"Value""" + str(count) + '": ' + value
        if count != (len(sqons)-1):
            json_refs = json_refs + ', '
            json_defs = json_defs + ', '

    sqon_json = json_refs_open + json_refs + json_refs_close + json_defs + schema_close

    return sqon_json

def format_sqon_filters(sqon_filters: str) -> str:
    """Format string into SQON format

    String from LLM may need to be slightly modified to be used 
    in a GraphQL query (i.e. single vs double quotes).

    Parameters
    ----------
    sqon_filters : str
        Raw Serializable Query Object Notation (SQON) 
        that need to be modified.

    Returns
    -------
    str
        String representation of SQON with quotes modified.
    """
    modified_filters = sqon_filters.replace("'", '"')
    for sqon_keyword in ['fieldName', 'value', 'op', 'content']:
        modified_filters = modified_filters.replace(
            '"'+sqon_keyword+'"', sqon_keyword
        )

    return modified_filters

@tool
def get_total_graphql(sqon_filters: str) -> str:
    """Get the total number of records in Arranger (via GraphQL) based on the SQON filters

    Parameters
    ----------
    sqon_filters : str
        Representation of Serializable Query Object Notation (SQON) 
        filters that are passed to the GraphQL query.

    Returns
    -------
    str of integer
        Total number of records in Arranger database that correspond to SQON filters.
    """
    json_response = query_graphql(sqon_filters)
    total = json.loads(json_response)['file']['hits']['total']

    return str(total)

def query_graphql(sqon_filters: str) -> str:
    """Query GraphQL endpoint with SQON filters

    Parameters
    ----------
    sqon_filters : str
        Representation of Serializable Query Object Notation (SQON) 
        filters that are passed to the GraphQL query

    Returns
    -------
    JSON as str
        Response from GraphQL query

    Notes
    -----
    Information about SQON filter notation can be found at Overtures website 
    (https://www.overture.bio/documentation/arranger/reference/sqon/)
    
    """

    graphql_query = f"{{file{{hits(filters:{sqon_filters}){{total}}}}}}"

    graphql = GraphQLAPIWrapper(
        # TODO: abstract this value into an EnvVar
        graphql_endpoint="https://arranger.virusseq-dataportal.ca/graphql"
    )
    response = graphql.run(query=graphql_query)

    return response
