"""Unit tests for validation helpers"""
from utils.response import (
    validate_email,
    validate_amount,
    validate_required_fields,
    sanitize_string,
    json_response,
)


class TestValidation:
    def test_validate_email(self):
        assert validate_email('user@example.com')
        assert not validate_email('not-an-email')
        assert not validate_email('')

    def test_validate_amount(self):
        assert validate_amount(10)
        assert validate_amount('5.5')
        assert not validate_amount(0)
        assert not validate_amount(-1)
        assert not validate_amount('abc')

    def test_validate_required_fields(self):
        ok, msg = validate_required_fields({'a': 1, 'b': 2}, ['a', 'b'])
        assert ok
        ok, msg = validate_required_fields({'a': 1}, ['a', 'b'])
        assert not ok
        assert 'b' in msg

    def test_sanitize_string(self):
        assert sanitize_string('  hello  ') == 'hello'
        assert sanitize_string('') == ''
        assert len(sanitize_string('x' * 3000)) == 2000

    def test_json_response(self):
        resp = json_response({'ok': True}, 201)
        assert resp['status_code'] == 201
        assert 'ok' in resp['body']
        assert resp['headers']['Content-Type'] == 'application/json'
