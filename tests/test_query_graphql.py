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
