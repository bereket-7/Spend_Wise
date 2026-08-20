"""Integration-style tests for auth controller"""
import json
from unittest.mock import Mock, patch

from controller.auth_controller import AuthController


def _handler(path, body):
    handler = Mock()
    handler.path = path
    raw = json.dumps(body).encode('utf-8')
    handler.headers = {'Content-Length': str(len(raw))}
    handler.rfile = Mock()
    handler.rfile.read.return_value = raw
    handler.auth_user = None
    return handler


class TestAuthController:
    def test_login_success(self):
        handler = _handler('/auth/login', {'username': 'u', 'password': 'p'})
        user = {
            'user_id': 1,
            'username': 'u',
            'email': 'u@e.com',
            'role': 'user',
        }
        with patch('controller.auth_controller.auth_manager.authenticate_user', return_value=user):
            with patch('controller.auth_controller.auth_manager.generate_token', return_value='tok'):
                ctrl = AuthController(handler, {})
                resp = ctrl.handle_post()
        assert resp['status_code'] == 200
        data = json.loads(resp['body'])
        assert data['token'] == 'tok'

    def test_login_invalid(self):
        handler = _handler('/auth/login', {'username': 'u', 'password': 'bad'})
        with patch('controller.auth_controller.auth_manager.authenticate_user', return_value=None):
            ctrl = AuthController(handler, {})
            resp = ctrl.handle_post()
        assert resp['status_code'] == 401

    def test_register_success(self):
        body = {
            'username': 'new',
            'password': 'pass123',
            'email': 'n@e.com',
            'first_name': 'N',
            'last_name': 'U',
        }
        handler = _handler('/auth/register', body)
        with patch('controller.auth_controller.user_query.get_user_by_username', return_value=None):
            with patch('controller.auth_controller.user_query.create_user', return_value=True):
                with patch('controller.auth_controller.auth_manager.hash_password', return_value='hashed'):
                    ctrl = AuthController(handler, {})
                    resp = ctrl.handle_post()
        assert resp['status_code'] == 201

    def test_register_duplicate(self):
        body = {
            'username': 'exists',
            'password': 'pass123',
            'email': 'n@e.com',
            'first_name': 'N',
            'last_name': 'U',
        }
        handler = _handler('/auth/register', body)
        with patch('controller.auth_controller.user_query.get_user_by_username', return_value=Mock()):
            ctrl = AuthController(handler, {})
            resp = ctrl.handle_post()
        assert resp['status_code'] == 409
