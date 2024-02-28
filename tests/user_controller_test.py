from user_controller import create_user, get_user_by_id, update_user, delete_user, get_all_users
from user import User

# Test create_user function
def test_create_user():
    # Create a user object with the necessary attributes
    user = User(username='beki', password='pass123', email='beki7@gmail.com', phone_number='0943578915', first_name='Bereket', last_name='Honelign', role='admin')
    result = create_user(user)
    if result:
        print("User creation successful!")
    else:
        print("User creation failed.")

# Test get_user_by_id function
def test_get_user_by_id(user_id):
    # Call the get_user_by_id function
    user = get_user_by_id(user_id)
    # Check the result
    if user is not None:
        print(f"User found: {user.username}")
    else:
        print("User not found.")

# Test update_user function
def test_update_user(user_id):
    # Get the existing user by ID
    user = get_user_by_id(user_id)
    
    if user is not None:
        # Update the user object with new values
        user.username = 'beka'
        user.password = 'pass12'
        result = update_user(user)
        if result:
            print("User update successful!")
        else:
            print("User update failed.")
    else:
        print("User not found.")

# Test delete_user function
def test_delete_user(user_id):
    # Call the delete_user function
    result = delete_user(user_id)
    # Check the result
    if result:
        print("User deletion successful!")
    else:
        print("User deletion failed.")

# Test get_all_users function
def test_get_all_users():
    users = get_all_users()
    if users is not None:
        print("Users found:")
        for user in users:
            print(user.username)
    else:
        print("No users found.")


# Execute the test functions
test_create_user()
test_get_user_by_id(1)  
#test_update_user(1)     
#test_delete_user(1)    
test_get_all_users()