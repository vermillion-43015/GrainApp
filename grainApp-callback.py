import json
import os
import urllib.request
import urllib.parse
import boto3
import base64

def handler(event, context):
    try:
        # Get authorization code
        params = event.get('queryStringParameters', {})
        code = params.get('code')
        
        if not code:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'text/html'},
                'body': '<h1>Error: No authorization code</h1>'
            }
        
        # Exchange code for tokens
        data = urllib.parse.urlencode({
            'grant_type': 'authorization_code',
            'client_id': os.environ['CLIENT_ID'],
            'code': code,
            'redirect_uri': os.environ['REDIRECT_URI']
        }).encode('utf-8')
        
        token_url = f"https://{os.environ['COGNITO_DOMAIN']}/oauth2/token"
        request = urllib.request.Request(token_url, data, method='POST')
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        with urllib.request.urlopen(request) as response:
            token_data = json.loads(response.read().decode('utf-8'))
        
        id_token = token_data['id_token']
        access_token = token_data['access_token']
        
        # Decode JWT
        payload = json.loads(base64.urlsafe_b64decode(id_token.split('.')[1] + '=='))
        username = payload['cognito:username']
        email = payload['email']
        
        # Get user groups
        cognito = boto3.client('cognito-idp')
        groups_response = cognito.admin_list_groups_for_user(
            UserPoolId=os.environ['USER_POOL_ID'],
            Username=username
        )
        
        groups = [g['GroupName'] for g in groups_response.get('Groups', [])]
        
        if 'Admins' in groups:
            role = 'Admin'
        elif 'Sellers' in groups:
            role = 'Seller'
        elif 'Buyers' in groups:
            role = 'Buyer'
        else:
            role = 'User'
        
        # Return redirect with tokens
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/html'},
            'body': f'''<!DOCTYPE html>
<html>
<head>
    <title>Login Success</title>
    <script>
        sessionStorage.setItem('id_token', '{id_token}');
        sessionStorage.setItem('access_token', '{access_token}');
        sessionStorage.setItem('user_email', '{email}');
        sessionStorage.setItem('user_role', '{role}');
        window.location.href = '/dashboard';
    </script>
</head>
<body>
    <p>Login successful. Redirecting...</p>
</body>
</html>'''
        }
        
    except Exception as ex:
        print(f"Error: {str(ex)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(ex)})
        }