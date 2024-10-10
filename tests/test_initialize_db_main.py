import pytest
import initialize_db.main

param_create_value_object_schema = [
    # baseline test
    (
        'analysis__host__host_gender',
        'Aggregations',
        None,
        [
            'Female', 'Male', 'Not Provided', 'Restricted Access',
            'Missing', 'Unknown', 'Undeclared'
        ],
        (
            (
                '{"type": "object", "required": ["value"], "properties": {"fieldName": {"const": '
                '"analysis.host.host_gender", "type": "string", "description": '
                '"analysis host host gender"}, "value": {"type": "array", "items": {"enum": ['
                '"Female", "Male", "Not Provided", "Restricted Access", '
                '"Missing", "Unknown", "Undeclared"'
                '], "type": "string"}, "minItems": 1}}}'
            ),
            'analysis host host gender',
            [
                'Female', 'Male', 'Not Provided', 'Restricted Access', 
                'Missing', 'Unknown', 'Undeclared'
            ]
        )
    ),
    # add description to baseline
    (
        'analysis__host__host_gender',
        'Aggregations',
        'test description',
        [
            'Female', 'Male', 'Not Provided', 'Restricted Access',
            'Missing', 'Unknown', 'Undeclared'
        ],
        (
            (
                '{"type": "object", "required": ["value"], "properties": {"fieldName": {"const": '
                '"analysis.host.host_gender", "type": "string", "description": '
                '"test description"}, "value": {"type": "array", "items": {"enum": ['
                '"Female", "Male", "Not Provided", "Restricted Access", '
                '"Missing", "Unknown", "Undeclared"'
                '], "type": "string"}, "minItems": 1}}}'
            ),
            'test description',
            [
                'Female', 'Male', 'Not Provided', 'Restricted Access',
                'Missing', 'Unknown', 'Undeclared'
            ]
        )
    ),
    # change enums
    (
        'analysis__host__host_gender',
        'Aggregations',
        None,
        [
            'Female', 'Male', 'Not Provided', 'Restricted Access',
            'Missing', 'Unknown'
        ],
        (
            (
                '{"type": "object", "required": ["value"], "properties": {"fieldName": {"const": '
                '"analysis.host.host_gender", "type": "string", "description": '
                '"analysis host host gender"}, "value": {"type": "array", "items": {"enum": ['
                '"Female", "Male", "Not Provided", "Restricted Access", '
                '"Missing", "Unknown"'
                '], "type": "string"}, "minItems": 1}}}'
            ),
            'analysis host host gender',
            [
                'Female', 'Male', 'Not Provided', 'Restricted Access',
                'Missing', 'Unknown'
            ]
        )
    ),
    # test NumericalAggregations fieldtype
    (
        'analysis__host__host_gender',
        'NumericalAggregations',
        None,
        [],
        (
            (
                '{"type": "object", "required": ["value"], "properties": {"fieldName": {"const": '
                '"analysis.host.host_gender", "type": "string", "description": '
                '"analysis host host gender"}, "value": {"type": "integer"}}}'
            ),
            'analysis host host gender',
            []
        )
    )
]

@pytest.mark.parametrize(
    'fieldname_1, fieldtype_1, description_1, get_enums_1, expected_result_1',
    param_create_value_object_schema
)

def test_create_value_object_schema(
    fieldname_1, fieldtype_1, description_1,
    get_enums_1, expected_result_1, monkeypatch
):
    def mock_get_enums(fieldname):
        return get_enums_1
    monkeypatch.setattr(
        initialize_db.main, 'get_enums', mock_get_enums
    )

    actual_result = initialize_db.main.create_value_object_schema(
        fieldname=fieldname_1, fieldtype=fieldtype_1, description=description_1
    )

    assert actual_result == expected_result_1
