class user:
    def __init__(self, user_id: int, username: str, password: str, email: str, phone_number: str, first_name: str, last_name: str, role: str):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.email = email
        self.phone_number = phone_number
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
