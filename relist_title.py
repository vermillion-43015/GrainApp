import json
import boto3
import hashlib
from datetime import datetime
from decimal import Decimal
from collections import defaultdict

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('GrainTitles')

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def get_user_info(event):
    try:
        claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        if not claims:
            return None
        email = claims.get('email', 'unknown@example.com')
        username = claims.get('cognito:username', 'unknown')
        user_sub = claims.get('sub', '')
        groups_claim = claims.get('cognito:groups', '')
        if isinstance(groups_claim, str):
            groups = [g.strip() for g in groups_claim.split(',')] if groups_claim else []
        else:
            groups = groups_claim if isinstance(groups_claim, list) else []
        is_admin = 'Admin' in groups or 'Admins' in groups
        return {
            'email': email,
            'username': username,
            'sub': user_sub,
            'groups': groups,
            'role': 'Admin' if is_admin else 'User',
            'is_admin': is_admin
        }
    except Exception as e:
        print(f"Error extracting user info: {str(e)}")
        return None

def lambda_handler(event, context):
    try:
        user_info = get_user_info(event)
        if not user_info:
            return {
                'statusCode': 401,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST'
                },
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        user_email = user_info['email']
        user_name = user_info['username']
        user_sub = user_info['sub']
        
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        print(f"Relist request from: {user_email}")
        
        title_hash = body.get('title_hash') or body.get('TitleHash') or body.get('titleHash')
        new_price = body.get('new_price') or body.get('newPrice') or body.get('price')
        
        if not title_hash:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST'
                },
                'body': json.dumps({'error': 'Missing title_hash'})
            }
        
        if new_price is None:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST'
                },
                'body': json.dumps({'error': 'Missing new_price'})
            }
        
        price_float = float(new_price)
        price_string = f"{price_float:.2f}"
        
        # Fetch current title with consistent read
        response = table.get_item(Key={'TitleHash': title_hash}, ConsistentRead=True)
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST'
                },
                'body': json.dumps({'error': 'Title not found'})
            }
        
        current_title = response['Item']
        
        # Check ownership
        seller_id = (current_title.get('SellerID') or '').lower()
        status = current_title.get('Status', '')
        
        if seller_id != user_email.lower():
            return {
                'statusCode': 403,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST'
                },
                'body': json.dumps({'error': 'You do not own this title'})
            }
        
        if status == 'ForSale':
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST'
                },
                'body': json.dumps({'error': 'Title is already for sale'})
            }
        
        # Get values from current record
        grain_type = current_title.get('GrainType')
        quantity = int(current_title.get('Quantity', 0))
        initial_hash = current_title.get('InitialHash', title_hash)
        current_hash = current_title.get('CurrentHash', title_hash)
        hash_chain = current_title.get('HashChain', [title_hash])
        current_transfer_count = int(current_title.get('TransferCount', 0))
        
        # NEW transfer count for the relist record
        new_transfer_count = current_transfer_count + 1
        
        # Generate timestamp
        timestamp = int(datetime.utcnow().timestamp())
        timestamp_iso = datetime.utcnow().isoformat()
        
        # Calculate new hash (includes previous hash for chain integrity)
        hash_input = f"{current_hash}{grain_type}{quantity}{user_email}{price_string}{timestamp_iso}{new_transfer_count}"
        new_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        print(f"Hash input: {hash_input}")
        print(f"New hash: {new_hash}")
        print(f"Transfer count: {new_transfer_count}")
        
        # Update hash chain
        new_hash_chain = hash_chain + [new_hash]
        
        # STEP 1: Mark the OLD record as "Listed" (it's been relisted)
        table.update_item(
            Key={'TitleHash': title_hash},
            UpdateExpression='SET #status = :status, RelistedAt = :timestamp, RelistedAtISO = :timestamp_iso',
            ExpressionAttributeNames={'#status': 'Status'},
            ExpressionAttributeValues={
                ':status': 'Listed',
                ':timestamp': timestamp,
                ':timestamp_iso': timestamp_iso
            }
        )
        
        # STEP 2: Create NEW record with new hash (blockchain style!)
        new_item = {
            'TitleHash': new_hash,
            'InitialHash': initial_hash,
            'CurrentHash': new_hash,
            'PreviousHash': current_hash,
            'HashChain': new_hash_chain,
            'GrainType': grain_type,
            'Quantity': quantity,
            'Price': Decimal(price_string),
            'PriceString': price_string,
            'SellerID': user_email,
            'SellerName': user_name,
            'SellerSub': user_sub,
            'BuyerID': 'NONE',
            'BuyerName': 'NONE',
            'BuyerSub': 'NONE',
            'Status': 'ForSale',
            'TransferCount': new_transfer_count,
            'HashTimestamp': timestamp_iso,
            'Timestamp': timestamp,
            'TimestampISO': timestamp_iso,
            'CreatedBy': current_title.get('CreatedBy', user_email),
            'CreatedBySub': current_title.get('CreatedBySub', ''),
            'CreatedByUsername': current_title.get('CreatedByUsername', ''),
            'RelistedBy': user_email,
            'RelistedFrom': title_hash
        }
        
        table.put_item(Item=new_item)
        
        print(f"Created new ForSale record with hash {new_hash}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'message': 'Title relisted successfully',
                'old_hash': title_hash,
                'new_hash': new_hash,
                'new_price': price_float,
                'transfer_count': new_transfer_count,
                'status': 'ForSale'
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({'error': str(e)})
        }

handler = lambda_handler