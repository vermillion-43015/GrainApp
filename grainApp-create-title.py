import json
import boto3
import hashlib
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('GrainTitles')

def get_user_info(event):
    """Extract user information from Cognito authorizer claims"""
    try:
        claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        
        if not claims:
            print("WARNING: No Cognito claims found in request")
            return None
        
        email = claims.get('email', 'unknown@example.com')
        username = claims.get('cognito:username', 'unknown')
        user_sub = claims.get('sub', '')  # Unique Cognito user ID
        
        # Extract groups
        groups_claim = claims.get('cognito:groups', '')
        if isinstance(groups_claim, str):
            groups = [g.strip() for g in groups_claim.split(',')] if groups_claim else []
        else:
            groups = groups_claim if isinstance(groups_claim, list) else []
        
        is_admin = 'Admin' in groups or 'Admins' in groups
        role = 'Admin' if is_admin else 'User'
        
        user_info = {
            'email': email,
            'username': username,
            'sub': user_sub,
            'groups': groups,
            'role': role,
            'is_admin': is_admin
        }
        
        print(f"User info extracted: {json.dumps(user_info)}")
        return user_info
        
    except Exception as e:
        print(f"Error extracting user info: {str(e)}")
        return None

def handler(event, context):
    try:
        # Extract user information - REQUIRED
        user_info = get_user_info(event)
        if not user_info:
            return {
                'statusCode': 401,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST'
                },
                'body': json.dumps({'error': 'Unauthorized: Could not extract user information'})
            }
        
        # Parse the request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        print(f"Received body: {json.dumps(body)}")
        print(f"User: {user_info['email']} ({user_info['role']})")
        
        # FORCE seller to be the logged-in user - no manual input allowed
        seller_id = user_info['email']
        seller_name = user_info['username']
        seller_sub = user_info['sub']  # Store Cognito sub for reliable identification
        
        # Extract fields from request - only grain_type, quantity, price allowed
        grain_type = body.get('grain_type') or body.get('GrainType')
        quantity = body.get('quantity') or body.get('Quantity')
        price = body.get('price') or body.get('Price')
        
        # Validate required fields
        if not grain_type:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST'
                },
                'body': json.dumps({'error': 'Missing grain_type'})
            }
        
        if not quantity:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST'
                },
                'body': json.dumps({'error': 'Missing quantity'})
            }
        
        if not price:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST'
                },
                'body': json.dumps({'error': 'Missing price'})
            }
        
        # Convert and validate types
        try:
            quantity_int = int(quantity)
            if quantity_int <= 0:
                raise ValueError("Quantity must be positive")
        except (ValueError, TypeError) as e:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST'
                },
                'body': json.dumps({'error': f'Invalid quantity: {str(e)}'})
            }
        
        # Normalize price to 2 decimal places for consistent hashing
        try:
            price_float = float(price)
            if price_float <= 0:
                raise ValueError("Price must be positive")
            price_normalized = f"{price_float:.2f}"
        except (ValueError, TypeError) as e:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST'
                },
                'body': json.dumps({'error': f'Invalid price: {str(e)}'})
            }
        
        # Generate timestamp
        timestamp = int(datetime.utcnow().timestamp())
        timestamp_iso = datetime.utcnow().isoformat()
        
        # Create initial hash
        hash_input = f"{grain_type}{quantity_int}{seller_id}{price_normalized}{timestamp_iso}"
        initial_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        print(f"Hash input: {hash_input}")
        print(f"Generated hash: {initial_hash}")
        
        current_hash = initial_hash
        previous_hash = initial_hash
        
        # Create the title item
        item = {
            'TitleHash': current_hash,
            'SellerID': seller_id,
            'SellerName': seller_name,
            'SellerSub': seller_sub,  # Cognito unique ID
            'BuyerID': 'NONE',
            'BuyerName': 'NONE',
            'BuyerSub': 'NONE',
            'GrainType': grain_type,
            'Quantity': quantity_int,
            'Price': Decimal(price_normalized),
            'PriceString': price_normalized,
            'Status': 'ForSale',
            'Timestamp': timestamp,
            'TimestampISO': timestamp_iso,
            'HashTimestamp': timestamp_iso,
            'InitialHash': initial_hash,
            'CurrentHash': current_hash,
            'PreviousHash': previous_hash,
            'TransferCount': 0,
            'HashChain': [initial_hash],
            'CreatedBy': user_info['email'],
            'CreatedByUsername': user_info['username'],
            'CreatedBySub': seller_sub
        }
        
        # Save to DynamoDB
        print(f"Saving item to DynamoDB...")
        table.put_item(Item=item)
        print(f"Successfully created title with ID: {current_hash}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'message': 'Title created successfully',
                'titleId': current_hash,
                'hash': current_hash,
                'initial_hash': initial_hash,
                'previous_hash': previous_hash,
                'status': 'Valid',
                'seller_id': seller_id,
                'seller_name': seller_name,
                'created_by': user_info['email']
            })
        }
        
    except Exception as e:
        print(f"ERROR in handler: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'error': str(e),
                'type': type(e).__name__
            })
        }

lambda_handler = handler