import os

def handler(event, context):
    cognito_domain = os.environ['COGNITO_DOMAIN']
    client_id = os.environ['CLIENT_ID']
    redirect_uri = os.environ['REDIRECT_URI']
    
    login_url = f"https://{cognito_domain}/login?client_id={client_id}&response_type=code&scope=email+openid+profile&redirect_uri={redirect_uri}"
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': f'''<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="1;url={login_url}">
    <title>Redirecting to Login</title>
</head>
<body style="text-align:center;padding:100px;font-family:Arial;">
    <h1>Grain Title Tracking</h1>
    <p>Redirecting to login...</p>
</body>
</html>'''
    }