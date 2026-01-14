import json
import boto3
from decimal import Decimal
from collections import defaultdict

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('GrainTitles')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

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
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,GET'
                },
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        user_email = user_info['email'].lower()
        print(f"Loading titles for user: {user_email}")
        
        # Scan entire table with consistent read
        response = table.scan(ConsistentRead=True)
        all_items = response.get('Items', [])
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey'],
                ConsistentRead=True
            )
            all_items.extend(response.get('Items', []))
        
        print(f"Total records: {len(all_items)}")
        
        # Group by InitialHash
        chains = defaultdict(list)
        for item in all_items:
            initial_hash = item.get('InitialHash', item.get('TitleHash'))
            chains[initial_hash].append(item)
        
        # Find chain heads owned by user
        my_titles = []
        for initial_hash, records in chains.items():
            # Sort by TransferCount DESC to get head
            records.sort(key=lambda x: int(x.get('TransferCount', 0)), reverse=True)
            head = records[0]
            
            seller_id = (head.get('SellerID') or '').lower()
            if seller_id == user_email:
                my_titles.append(head)
        
        print(f"User owns {len(my_titles)} chain heads")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            'body': json.dumps({
                'items': my_titles,
                'count': len(my_titles),
                'user_email': user_email
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            'body': json.dumps({'error': str(e)})
        }

handler = lambda_handler