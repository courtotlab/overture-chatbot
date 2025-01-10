"""
   Copyright 2025 Ontario Institute for Cancer Research

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

"""Tests for overture_chatbot.query_graphql"""

import pytest
import overture_chatbot.query_graphql

param_query_total_chain = [
    (
        'Find the number of males',
        '207571'
    )
]

@pytest.mark.parametrize(
    'query_1, expected_result_1',
    param_query_total_chain
)

def test_query_total_chain(
    query_1, expected_result_1
):
    """Test for overture_chatbot.query_graphql.query_total_chain"""
    chain = overture_chatbot.query_graphql.query_total_chain()
    actual_result = chain.invoke(query_1)

    assert actual_result == expected_result_1


def test_create_sqon_schema():
    """Test for overture_chatbot.query_graphql.create_sqon_schema"""
    query = "Filter for males in the database"
    expected_create_sqon_schema = (
        "{'op': 'and', 'content': [{'op': 'in', 'content': "
        "{'fieldName': 'analysis.host.host_gender', 'value': ['Male']}}]}"
    )

    chain = overture_chatbot.query_graphql.create_sqon_schema()
    actual_result = chain.invoke({'query': query})

    assert actual_result == expected_create_sqon_schema


def test_get_keyword_chain():
    """Test for overture_chatbot.query_graphql.get_keyword_chain"""
    query = 'Find the number of samples in Labrador not collected from men'
    expected_get_keyword_chain = 'Labrador, men'

    chain = overture_chatbot.query_graphql.get_keyword_chain()
    actual_result = chain.invoke({'query': query})

    assert actual_result == expected_get_keyword_chain


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
    """Test for overture_chatbot.query_graphql.format_sqon_schema"""
    actual_result = overture_chatbot.query_graphql.format_sqons_schema(sqons_2)

    assert actual_result == expected_sqons_schema_2


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
    'sqon_filter_str_3, expected_format_sqon_filters_3', 
    param_format_sqon_filters
)

def test_format_sqon_filters(
    sqon_filter_str_3, expected_format_sqon_filters_3
):
    """Test for overture_chatbot.query_graphql.format_sqon_filters"""
    actual_result = overture_chatbot.query_graphql.format_sqon_filters(sqon_filter_str_3)

    assert actual_result == expected_format_sqon_filters_3


def test_get_total_graphql(monkeypatch):
    """Test for overture_chatbot.query_graphql.get_total_graphql"""
    sqon_filters = ''
    expected_get_total_graphql = '100'

    def mock_query_graphql(sqon_filters):
        result = '{"file": {"hits": {"total": 100}}}'
        return result
    monkeypatch.setattr(overture_chatbot.query_graphql, 'query_graphql', mock_query_graphql)

    actual_result = overture_chatbot.query_graphql.get_total_graphql(sqon_filters)

    assert actual_result == expected_get_total_graphql


def test_query_graphql():
    """Test for overture_chatbot.query_graphql.query_graphql"""
    sqon_filter = (
        '{op: "and", content: [{op: "in", content: '
        '{fieldName: "analysis.host.host_gender", value: ["Male"]}}]}'
    )
    expected_query_graphql = '{\n  "file": {\n    "hits": {\n      "total": 207571\n    }\n  }\n}'

    actual_result = overture_chatbot.query_graphql.query_graphql(sqon_filter)

    assert actual_result == expected_query_graphql
