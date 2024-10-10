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

def test_create_sqon_schema():
    query = "Filter for males in the database"
    expected_create_sqon_schema = (
        "{'op': 'and', 'content': [{'op': 'in', 'content': "
        "{'fieldName': 'analysis.host.host_gender', 'value': ['Male']}}]}"
    )

    chain = overture_chatbot.query_graphql.create_sqon_schema()
    actual_result = chain.invoke({'query': query})

    assert actual_result == expected_create_sqon_schema

def test_query_graphql():
    sqon_filter = (
        '{op: "and", content: [{op: "in", content: '
        '{fieldName: "analysis.host.host_gender", value: ["Male"]}}]}'
    )
    expected_query_graphql = '{\n  "file": {\n    "hits": {\n      "total": 207094\n    }\n  }\n}'

    actual_result = overture_chatbot.query_graphql.query_graphql(sqon_filter)

    assert actual_result == expected_query_graphql

param_format_sqon_schema = [
    (
        [],
        (
            '{{"type": "object", "required": ["content", "op"], "properties": {{"content": '
            '{{"type": "array", "items": {{"oneOf": [{{"$ref": "#/$defs/FieldOperations"}}, '
            '{{"$ref": "#"}}]}}, "minItems": 1}}, "op": {{"default": "and", '
            '"enum": ["and", "or", "not"], "type": "string"}}}}, "$defs": '
            '{{"FieldOperations": {{"type": "object", "required": ["content", "op"], '
            '"properties": {{"content": {{"type": "array", "items": {{"oneOf": ['
            ''
            ']}}, "maxItems": 1, "minItems": 1}}, "op": {{"default": "in", '
            '"enum": ["in", "<=", ">="], "type": "string"}}}}}}, '
            ''
            '}}}}}'
        )
    ),
    (
        ['A'],
        (
            '{{"type": "object", "required": ["content", "op"], "properties": {{"content": '
            '{{"type": "array", "items": {{"oneOf": [{{"$ref": "#/$defs/FieldOperations"}}, '
            '{{"$ref": "#"}}]}}, "minItems": 1}}, "op": {{"default": "and", '
            '"enum": ["and", "or", "not"], "type": "string"}}}}, "$defs": '
            '{{"FieldOperations": {{"type": "object", "required": ["content", "op"], '
            '"properties": {{"content": {{"type": "array", "items": {{"oneOf": ['
            """{{"$ref": "#/$defs/Value""" + str(0) + """"}}"""
            ']}}, "maxItems": 1, "minItems": 1}}, "op": {{"default": "in", '
            '"enum": ["in", "<=", ">="], "type": "string"}}}}}}, '
            """"Value""" + str(0) + '": ' + 'A'
            '}}}}}'
        )
    ),
    (
        ['A', 'B', 'C'],
        (
            '{{"type": "object", "required": ["content", "op"], "properties": {{"content": '
            '{{"type": "array", "items": {{"oneOf": [{{"$ref": "#/$defs/FieldOperations"}}, '
            '{{"$ref": "#"}}]}}, "minItems": 1}}, "op": {{"default": "and", '
            '"enum": ["and", "or", "not"], "type": "string"}}}}, "$defs": '
            '{{"FieldOperations": {{"type": "object", "required": ["content", "op"], '
            '"properties": {{"content": {{"type": "array", "items": {{"oneOf": ['
            """{{"$ref": "#/$defs/Value""" + str(0) + """"}}""" + ', '
            """{{"$ref": "#/$defs/Value""" + str(1) + """"}}""" + ', '
            """{{"$ref": "#/$defs/Value""" + str(2) + """"}}"""
            ']}}, "maxItems": 1, "minItems": 1}}, "op": {{"default": "in", '
            '"enum": ["in", "<=", ">="], "type": "string"}}}}}}, '
            """"Value""" + str(0) + '": ' + 'A' + ', '
            """"Value""" + str(1) + '": ' + 'B' + ', '
            """"Value""" + str(2) + '": ' + 'C'
            '}}}}}'
        )
    ),
]

@pytest.mark.parametrize(
    'sqons_2, expected_sqons_schema_2', 
    param_format_sqon_schema
)

def test_format_sqons_schema(
    sqons_2, expected_sqons_schema_2
):
    actual_result = overture_chatbot.query_graphql.format_sqons_schema(sqons_2)

    assert actual_result == expected_sqons_schema_2

param_query_total_chain = [
    (
        'Find the number of males',
        '207094'
    )
]

@pytest.mark.parametrize(
    'query_3, expected_result_3',
    param_query_total_chain
)

def test_query_total_chain(
    query_3, expected_result_3
):
    chain = overture_chatbot.query_graphql.query_total_chain()
    actual_result = chain.invoke(query_3)

    assert actual_result == expected_result_3