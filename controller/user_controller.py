import json
from utils import api_service
from response import json_response
import user_query

class UserController(api_service):
    def handle_get(self):
        if self.path.startswith('/users/'):
            user_id = int(self.path.split('/')[-1])
            user = user_query.get_user_by_id(user_id)

            if user is not None:
                user_data = {
                    'user_id': user.user_id,
                    'username': user.username,
                    'email': user.email,
                    'phone_number': user.phone_number,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role
                }
                return json_response(user_data)
            else:
                return json_response({'message': 'User not found'}, status_code=404)
        elif self.path == '/users':
            users = user_query.get_all_users()

            if users is not None:
                users_data = []
                for user in users:
                    user_data = {
                        'user_id': user.user_id,
                        'username': user.username,
                        'email': user.email,
                        'phone_number': user.phone_number,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'role': user.role
                    }
                    users_data.append(user_data)

                return json_response(users_data)
            else:
                return json_response({'message': 'No users found'}, status_code=404)
        else:
            return json_response({'message': 'Not found'}, status_code=404)

    def handle_post(self):
        if self.path == '/users':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            user_data = json.loads(body)

            user = user(
                username=user_data['username'],
                password=user_data['password'],
                email=user_data['email'],
                phone_number=user_data['phone_number'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role']
            )
            result = user_query.create_user(user)

            if result:
                return json_response({'message': 'User created successfully'}, status_code=201)
            else:
                return json_response({'message': 'Failed to create user'}, status_code=500)
        else:
            return json_response({'message': 'Not found'}, status_code=404)
        

    def handle_put(self):
        if self.path.startswith('/users/'):
            user_id = int(self.path.split('/')[-1])
            user = user_query.get_user_by_id(user_id)

            if user is not None:
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                user_data = json.loads(body)

                user.username = user_data.get('username', user.username)
                user.password = user_data.get('password', user.password)
                user.email = user_data.get('email', user.email)
                user.phone_number = user_data.get('phone_number', user.phone_number)
                user.first_name = user_data.get('first_name', user.first_name)
                user.last_name = user_data.get('last_name', user.last_name)

                result = user_query.update_user(user)

                if result:
                    return json_response({'message': 'User updated successfully'})
                else:
                    return json_response({'message': 'Failed to update user'}, status_code=500)
            else:
                return json_response({'message': 'User not found'}, status_code=404)
        else:
            return json_response({'message': 'Not found'}, status_code=404)

    def handle_delete(self):
        if self.path.startswith('/users/'):
            user_id = int(self.path.split('/')[-1])
            user = user_query.get_user_by_id(user_id)

            if user is not None:
                result = user_query.delete_user(user_id)

                if result:
                    return json_response({'message': 'User deleted successfully'})
                else:
                    return json_response({'message': 'Failed to delete user'}, status_code=500)
            else:
                return json_response({'message': 'User not found'}, status_code=404)
        else:
            return json_response({'message': 'Not found'}, status_code=404)