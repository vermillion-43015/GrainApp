import os

def handler(event, context):
    cognito_domain = os.environ['COGNITO_DOMAIN']
    client_id = os.environ['CLIENT_ID']
    redirect_uri = os.environ['REDIRECT_URI']
    
    login_url = f"https://{cognito_domain}/login?client_id={client_id}&response_type=code&scope=email+openid+profile&redirect_uri={redirect_uri}"
    signup_url = f"https://{cognito_domain}/signup?client_id={client_id}&response_type=code&scope=email+openid+profile&redirect_uri={redirect_uri}"
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grain Title Tracking - Login</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            background: linear-gradient(135deg, #3a3a3a 0%, #4d4d4d 50%, #606060 100%); 
            min-height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            padding: 20px;
        }}
        .login-container {{ 
            background: white; 
            border-radius: 15px; 
            box-shadow: 0 20px 60px rgba(0,0,0,0.3); 
            padding: 50px; 
            text-align: center;
            max-width: 450px;
            width: 100%;
        }}
        h1 {{ 
            color: #2c5282; 
            margin-bottom: 10px; 
            font-size: 2em;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 40px;
            font-size: 1.1em;
        }}
        .btn {{
            display: block;
            width: 100%;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            margin-bottom: 15px;
        }}
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #3d6ba8 0%, #2c5282 100%);
            color: white;
        }}
        .btn-primary:hover {{
            background: linear-gradient(135deg, #4a7ab8 0%, #3d6ba8 100%);
        }}
        .btn-success {{
            background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
            color: white;
        }}
        .btn-success:hover {{
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        }}
        .btn-guest {{
            background: #f8f9fa;
            color: #333;
            border: 2px solid #dee2e6;
        }}
        .btn-guest:hover {{
            background: #e9ecef;
            border-color: #adb5bd;
        }}
        .divider {{
            display: flex;
            align-items: center;
            margin: 25px 0;
            color: #999;
        }}
        .divider::before, .divider::after {{
            content: "";
            flex: 1;
            border-bottom: 1px solid #dee2e6;
        }}
        .divider span {{
            padding: 0 15px;
            font-size: 0.9em;
        }}
        .guest-note {{
            font-size: 0.85em;
            color: #888;
            margin-top: 5px;
        }}
        .auth-buttons {{
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
        }}
        .auth-buttons .btn {{
            flex: 1;
            margin-bottom: 0;
        }}
    </style>
</head>
<body>
    <div class="login-container">
        <h1>Grain Title Tracking</h1>
        <p class="subtitle">Blockchain-Style Ownership Records</p>
        
        <div class="auth-buttons">
            <a href="{login_url}" class="btn btn-primary">Sign In</a>
            <a href="{signup_url}" class="btn btn-success">Register</a>
        </div>
        
        <div class="divider"><span>or</span></div>
        
        <button class="btn btn-guest" onclick="guestLogin()">Continue as Guest</button>
        <p class="guest-note">View marketplace only - no buying or selling</p>
    </div>
    
    <script>
        // Check if already logged in
        if (sessionStorage.getItem("id_token") || sessionStorage.getItem("is_guest") === "true") {{
            window.location.href = "/dashboard";
        }}
        
        function guestLogin() {{
            sessionStorage.setItem("is_guest", "true");
            sessionStorage.setItem("user_email", "Guest");
            sessionStorage.setItem("user_role", "Guest");
            window.location.href = "/dashboard";
        }}
    </script>
</body>
</html>'''
    }