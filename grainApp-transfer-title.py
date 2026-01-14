import json
import boto3
import hashlib
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('GrainTitles')

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def get_user_info(event):
    """Extract user information from Cognito authorizer claims"""
    try:
        claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        
        if not claims:
            print("WARNING: No Cognito claims found in request")
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
        role = 'Admin' if is_admin else 'User'
        
        return {
            'email': email,
            'username': username,
            'sub': user_sub,
            'groups': groups,
            'role': role,
            'is_admin': is_admin
        }
        
    except Exception as e:
        print(f"Error extracting user info: {str(e)}")
        return None

def lambda_handler(event, context):
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
        
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        print(f"Transfer request from: {user_info['email']}")
        print(f"Request body: {json.dumps(body)}")
        
        # Get title hash from request
        title_hash = body.get('title_hash') or body.get('TitleHash') or body.get('titleHash')
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
        
        # FORCE buyer to be the logged-in user
        buyer_id = user_info['email']
        buyer_name = user_info['username']
        buyer_sub = user_info['sub']
        
        # Fetch the current title
        response = table.get_item(Key={'TitleHash': title_hash},
                                        ConsistentRead=True)
        
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
        
        # Check if title is for sale
        if current_title.get('Status') != 'ForSale':
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST'
                },
                'body': json.dumps({'error': 'Title is not available for purchase'})
            }
        
        # Prevent buying your own title - only check SellerID (email)
        current_seller_id = current_title.get('SellerID', '')
        
        if buyer_id.lower() == current_seller_id.lower():
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST'
                },
                'body': json.dumps({'error': 'You cannot purchase your own title'})
            }
        
        # Get current values
        grain_type = current_title.get('GrainType')
        quantity = int(current_title.get('Quantity', 0))
        current_price = float(current_title.get('Price', 0))
        price_string = current_title.get('PriceString', f"{current_price:.2f}")
        initial_hash = current_title.get('InitialHash', title_hash)
        current_hash = current_title.get('CurrentHash', title_hash)
        hash_chain = current_title.get('HashChain', [title_hash])
        
        # Get the current transfer count and increment for the new record
        current_transfer_count = int(current_title.get('TransferCount', 0))
        new_transfer_count = current_transfer_count + 1
        
        # Generate new timestamp
        timestamp = int(datetime.utcnow().timestamp())
        timestamp_iso = datetime.utcnow().isoformat()
        
        # Calculate new hash (includes previous hash for chain integrity)
        hash_input = f"{current_hash}{grain_type}{quantity}{buyer_id}{price_string}{timestamp_iso}{new_transfer_count}"
        new_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        print(f"New hash input: {hash_input}")
        print(f"New hash: {new_hash}")
        print(f"Transfer count: {new_transfer_count}")
        
        # Update hash chain
        new_hash_chain = hash_chain + [new_hash]
        
        # STEP 1: Update the OLD record to mark as Transferred and record buyer
        table.update_item(
            Key={'TitleHash': title_hash},
            UpdateExpression='''SET 
                #status = :status,
                BuyerID = :buyer_id,
                BuyerName = :buyer_name,
                BuyerSub = :buyer_sub,
                LastTransferTimestamp = :timestamp,
                LastTransferTimestampISO = :timestamp_iso
            ''',
            ExpressionAttributeNames={
                '#status': 'Status'
            },
            ExpressionAttributeValues={
                ':status': 'Transferred',
                ':buyer_id': buyer_id,
                ':buyer_name': buyer_name,
                ':buyer_sub': buyer_sub,
                ':timestamp': timestamp,
                ':timestamp_iso': timestamp_iso
            }
        )
        
        # STEP 2: Create NEW record with new hash (this preserves the chain!)
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
            'SellerID': buyer_id,  # Buyer becomes new seller/owner
            'SellerName': buyer_name,
            'SellerSub': buyer_sub,
            'BuyerID': 'NONE',
            'BuyerName': 'NONE',
            'BuyerSub': 'NONE',
            'Status': 'Transferred',  # Not for sale until relisted
            'TransferCount': new_transfer_count,
            'HashTimestamp': timestamp_iso,
            'Timestamp': timestamp,
            'TimestampISO': timestamp_iso,
            'LastTransferTimestamp': timestamp,
            'LastTransferTimestampISO': timestamp_iso,
            'CreatedBy': current_title.get('CreatedBy', current_seller_id),
            'CreatedBySub': current_title.get('CreatedBySub', ''),
            'CreatedByUsername': current_title.get('CreatedByUsername', ''),
            'TransferredBy': current_seller_id,
            'TransferredTo': buyer_id
        }
        
        table.put_item(Item=new_item)
        
        print(f"Title transferred successfully to {buyer_id}")
        print(f"Old record {title_hash} marked as Transferred")
        print(f"New record created with hash {new_hash}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'message': 'Title transferred successfully',
                'old_hash': title_hash,
                'new_hash': new_hash,
                'previous_hash': current_hash,
                'buyer_id': buyer_id,
                'seller_id': current_seller_id,
                'transfer_count': new_transfer_count,
                'new_status': 'Transferred'
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"ERROR in transfer: {str(e)}")
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

handler = lambda_handler