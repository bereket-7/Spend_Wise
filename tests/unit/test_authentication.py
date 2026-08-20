"""Unit tests for authentication manager"""
import hashlib
from unittest.mock import patch, MagicMock

from utils.authentication import AuthenticationManager, TokenValidationMiddleware, auth_manager


class TestAuthenticationManager:
    def setup_method(self):
        self.auth = AuthenticationManager()

    def test_hash_password_bcrypt(self):
        hashed = self.auth.hash_password('secret123')
        assert hashed.startswith('$2')
        assert self.auth.verify_password('secret123', hashed)
        assert not self.auth.verify_password('wrong', hashed)

    def test_verify_legacy_sha256(self):
        password = 'admin123'
        legacy = hashlib.sha256(password.encode()).hexdigest()
        assert self.auth.verify_password(password, legacy)
        assert not self.auth.verify_password('wrong', legacy)

    def test_generate_and_verify_token(self):
        user = {
            'user_id': 1,
            'username': 'alice',
            'email': 'a@example.com',
            'role': 'user',
        }
        token = self.auth.generate_token(user)
        assert isinstance(token, str)
        payload = self.auth.verify_token(token)
        assert payload['user_id'] == 1
        assert payload['username'] == 'alice'

    def test_verify_invalid_token(self):
        assert self.auth.verify_token('not-a-token') is None

    def test_extract_token_from_header(self):
        assert self.auth.extract_token_from_header('Bearer abc.def.ghi') == 'abc.def.ghi'
        assert self.auth.extract_token_from_header('Basic xxx') is None
        assert self.auth.extract_token_from_header('') is None

    def test_authorize_roles(self):
        assert self.auth.authorize({'role': 'admin'}, 'admin')
        assert self.auth.authorize({'role': 'user'}, 'user')
        assert self.auth.authorize({'role': 'admin'}, 'user')
        assert not self.auth.authorize({'role': 'user'}, 'admin')
        assert not self.auth.authorize(None, 'user')

    def test_authenticate_user_success(self):
        hashed = self.auth.hash_password('pass')
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            'user_id': 1,
            'username': 'bob',
            'email': 'b@example.com',
            'phone_number': '',
            'first_name': 'Bob',
            'last_name': 'B',
            'role': 'user',
            'password': hashed,
        }
        with patch('utils.authentication.get_connection', return_value=mock_conn):
            with patch('utils.authentication.release_connection'):
                result = self.auth.authenticate_user('bob', 'pass')
        assert result is not None
        assert result['username'] == 'bob'

    def test_authenticate_user_bad_password(self):
        hashed = self.auth.hash_password('pass')
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            'user_id': 1,
            'username': 'bob',
            'email': 'b@example.com',
            'phone_number': '',
            'first_name': 'Bob',
            'last_name': 'B',
            'role': 'user',
            'password': hashed,
        }
        with patch('utils.authentication.get_connection', return_value=mock_conn):
            with patch('utils.authentication.release_connection'):
                result = self.auth.authenticate_user('bob', 'wrong')
        assert result is None

    def test_legacy_migration_on_login(self):
        password = 'legacy'
        legacy_hash = hashlib.sha256(password.encode()).hexdigest()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            'user_id': 2,
            'username': 'legacy',
            'email': 'l@example.com',
            'phone_number': '',
            'first_name': 'L',
            'last_name': 'U',
            'role': 'user',
            'password': legacy_hash,
        }
        with patch('utils.authentication.get_connection', return_value=mock_conn):
            with patch('utils.authentication.release_connection'):
                result = self.auth.authenticate_user('legacy', password)
        assert result is not None
        update_calls = [
            c for c in mock_cursor.execute.call_args_list
            if isinstance(c[0][0], str) and c[0][0].startswith('UPDATE user SET password')
        ]
        assert len(update_calls) == 1
        assert update_calls[0][0][1][1] == 2
        assert update_calls[0][0][1][0].startswith('$2')


class TestTokenValidationMiddleware:
    def test_missing_header(self):
        handler = MagicMock()
        handler.headers.get.return_value = None
        ok, err = TokenValidationMiddleware.validate_request(handler)
        assert not ok
        assert 'Missing' in err['message']

    def test_valid_token(self):
        token = auth_manager.generate_token({
            'user_id': 1,
            'username': 'u',
            'email': 'u@e.com',
            'role': 'user',
        })
        handler = MagicMock()
        handler.headers.get.return_value = f'Bearer {token}'
        ok, data = TokenValidationMiddleware.validate_request(handler)
        assert ok
        assert data['user_id'] == 1
