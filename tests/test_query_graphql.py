import pytest
import overture_chatbot.query_graphql

param_format_sqon_filters = [
    ('test', 'test'),
    ("'test'", '"test"'),
    ('"test"', '"test"'),
    ("te'st", 'te"st'),
    ('"fieldName"', 'fieldName'),
    (' "fieldName" ', ' fieldName '),
    ('"fieldName", "value"', 'fieldName, value')
]

@pytest.mark.parametrize(
    'sqon_filter_str_1, expected_format_sqon_filters_1', 
    param_format_sqon_filters
)

def test_format_sqon_filters(
    sqon_filter_str_1, expected_format_sqon_filters_1
):
    actual_result = overture_chatbot.query_graphql.format_sqon_filters(sqon_filter_str_1)

    assert actual_result == expected_format_sqon_filters_1

def test_get_total_graphql(monkeypatch):
    sqon_filters = ''
    expected_get_total_graphql = '100'
    
    def mock_query_graphql(sqon_filters):
        result = '{"file": {"hits": {"total": 100}}}'
        return result
    monkeypatch.setattr(overture_chatbot.query_graphql, 'query_graphql', mock_query_graphql)

    actual_result = overture_chatbot.query_graphql.get_total_graphql(sqon_filters)

    assert actual_result == expected_get_total_graphql

def test_get_keyword_chain():
    query = 'Find the number of samples in Labrador not collected from men'
    expected_get_keyword_chain = 'Labrador, men'

    chain = overture_chatbot.query_graphql.get_keyword_chain()
    actual_result = chain.invoke({'query': query})

    assert actual_result == expected_get_keyword_chain
