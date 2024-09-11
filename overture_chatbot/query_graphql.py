import json
from langchain_community.utilities.graphql import GraphQLAPIWrapper

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
