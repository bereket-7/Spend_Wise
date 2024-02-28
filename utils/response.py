import json

def json_response(data, status_code=200):
    return {
        'status_code': status_code,
        'body': json.dumps(data),
        'headers': {
            'Content-Type': 'application/json'
        }
    }