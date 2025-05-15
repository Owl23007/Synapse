import requests

headers = {
    'X-API-Key': 'iI6wm3gtM7aBDX12EyUKrvfLZWYRJQbF',
    'Content-Type': 'application/json'
}

data = {
    'message': '你好',
    'user_id': 'user123'
}

response = requests.post('http://localhost:2333/api/v1/agent', 
                        json=data, 
                        headers=headers)

print(response.text)