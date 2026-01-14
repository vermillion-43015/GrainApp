import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
titles_table = dynamodb.Table('GrainTitles')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

def get_user_info(event):
    """Extract user information from Cognito authorizer claims"""
    try:
        claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        
        if not claims:
            print("WARNING: No Cognito claims found in request")
            return None
        
        email = claims.get('email', 'unknown@example.com')
        username = claims.get('cognito:username', 'unknown')
        
        # Extract groups
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
            'groups': groups,
            'role': role,
            'is_admin': is_admin
        }
        
    except Exception as e:
        print(f"Error extracting user info: {str(e)}")
        return None

def lambda_handler(event, context):
    try:
        # Extract and verify user is admin
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
                'body': json.dumps({'error': 'Unauthorized: Could not extract user information'})
            }
        
        # CRITICAL: Check if user is admin
        if not user_info['is_admin']:
            print(f"Access denied for non-admin user: {user_info['email']}")
            return {
                'statusCode': 403,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,GET'
                },
                'body': json.dumps({
                    'error': 'Forbidden: Admin access required',
                    'user_role': user_info['role']
                })
            }
        
        print(f"Admin access granted for: {user_info['email']}")
        
        # Scan all titles to get statistics
        response = titles_table.scan()
        all_titles = response['Items']
        
        # Handle pagination if there are more items
        while 'LastEvaluatedKey' in response:
            response = titles_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            all_titles.extend(response['Items'])
        
        # Calculate statistics
        total_titles = len(all_titles)
        
        # Count by status
        for_sale = sum(1 for t in all_titles if t.get('Status') == 'ForSale')
        transferred = sum(1 for t in all_titles if t.get('Status') == 'Transferred')
        
        # Count by grain type
        grain_counts = {}
        for title in all_titles:
            grain = title.get('GrainType', 'Unknown')
            grain_counts[grain] = grain_counts.get(grain, 0) + 1
        
        # Total quantity and value
        total_quantity = sum(int(t.get('Quantity', 0)) for t in all_titles)
        total_value = sum(
            float(t.get('Price', 0)) * int(t.get('Quantity', 0)) 
            for t in all_titles
        )
        
        # Count transfers
        total_transfers = sum(int(t.get('TransferCount', 0)) for t in all_titles)
        
        # Get unique users (creators)
        unique_users = set()
        for title in all_titles:
            if 'CreatedBy' in title:
                unique_users.add(title['CreatedBy'])
            elif 'SellerID' in title:
                unique_users.add(title['SellerID'])
        
        # Count original titles (TransferCount = 0)
        original_titles = sum(1 for t in all_titles if int(t.get('TransferCount', 0)) == 0)
        
        stats = {
            'system_stats': {
                'total_titles': total_titles,
                'original_titles': original_titles,
                'total_transfers': total_transfers,
                'unique_users': len(unique_users)
            },
            'status_breakdown': {
                'for_sale': for_sale,
                'transferred': transferred
            },
            'grain_type_breakdown': grain_counts,
            'volume_stats': {
                'total_bushels': total_quantity,
                'total_value_usd': round(total_value, 2),
                'average_price_per_bushel': round(total_value / total_quantity, 2) if total_quantity > 0 else 0
            },
            'requested_by': user_info['email'],
            'timestamp': event.get('requestContext', {}).get('requestTimeEpoch', 0)
        }
        
        print(f"Statistics generated: {json.dumps(stats, cls=DecimalEncoder)}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            'body': json.dumps(stats, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Error generating statistics: {str(e)}")
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