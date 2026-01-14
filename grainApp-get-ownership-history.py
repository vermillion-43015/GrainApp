import json
import boto3
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('GrainTitles')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

def lambda_handler(event, context):
    try:
        # Parse request
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
        title_hash = body.get('title_hash')
        
        if not title_hash:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'title_hash is required'})
            }
        
        print(f"Looking up ownership history for TitleHash: {title_hash}")
        
        # First, get the clicked record to find its InitialHash
        response = table.get_item(Key={'TitleHash': title_hash})
        
        if 'Item' not in response:
            print(f"Title hash {title_hash} not found")
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Title not found', 'ownership_history': []})
            }
        
        initial_hash = response['Item'].get('InitialHash')
        
        if not initial_hash:
            print("No InitialHash found in record")
            # Return single item formatted properly
            formatted_record = format_record(response['Item'], is_current=True)
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'ownership_history': [formatted_record]}, cls=DecimalEncoder)
            }
        
        print(f"InitialHash: {initial_hash}")
        
        # Scan for all records with this InitialHash
        history_response = table.scan(
            FilterExpression='InitialHash = :initial_hash',
            ExpressionAttributeValues={':initial_hash': initial_hash}
        )
        
        history_items = history_response.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in history_response:
            history_response = table.scan(
                FilterExpression='InitialHash = :initial_hash',
                ExpressionAttributeValues={':initial_hash': initial_hash},
                ExclusiveStartKey=history_response['LastEvaluatedKey']
            )
            history_items.extend(history_response.get('Items', []))
        
        print(f"Found {len(history_items)} records in chain")
        
        # Sort by TransferCount to show chronological order
        history_items.sort(key=lambda x: int(x.get('TransferCount', 0)))
        
        # Format each record for the dashboard
        formatted_history = []
        for idx, item in enumerate(history_items):
            is_current = (item.get('TitleHash') == title_hash)
            formatted_record = format_record(item, is_current=is_current)
            formatted_history.append(formatted_record)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'ownership_history': formatted_history,
                'total_transfers': len(formatted_history) - 1 if formatted_history else 0
            }, cls=DecimalEncoder)
        }
        
    except Exception as ex:
        print(f"Error: {str(ex)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(ex), 'ownership_history': []})
        }

def format_record(item, is_current=False):
    """Format DynamoDB record for dashboard display"""
    
    # Get price
    price = float(item.get('PriceString') or item.get('Price') or 0)
    quantity = int(item.get('Quantity') or 0)
    total_value = price * quantity
    transfer_count = int(item.get('TransferCount') or 0)
    status = item.get('Status', '')
    
    # Format timestamp
    timestamp = item.get('HashTimestamp') or item.get('CreatedAt') or item.get('TimestampISO') or ''
    try:
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            timestamp_readable = dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            timestamp_readable = 'Unknown'
    except:
        timestamp_readable = timestamp or 'Unknown'
    
    seller_id = item.get('SellerID') or 'Unknown'
    buyer_id = item.get('BuyerID') or 'NONE'
    created_by = item.get('CreatedBy') or seller_id
    transferred_by = item.get('TransferredBy', '')
    transferred_to = item.get('TransferredTo', '')
    
    # Determine owner based on record type:
    if transfer_count == 0:
        # Original record - owner is the creator
        owner_display = created_by
        sold_to = buyer_id if buyer_id != 'NONE' else None
    else:
        # Transfer record - owner is SellerID (the person who received the transfer)
        owner_display = seller_id
        sold_to = buyer_id if buyer_id != 'NONE' else None
    
    return {
        'hash': item.get('TitleHash') or item.get('CurrentHash'),
        'owner': owner_display,
        'seller_id': seller_id,
        'created_by': created_by,
        'buyer_id': buyer_id,
        'sold_to': sold_to,
        'transferred_by': transferred_by,
        'transferred_to': transferred_to,
        'grain_type': item.get('GrainType'),
        'quantity': quantity,
        'price': price,
        'total_value': total_value,
        'timestamp_readable': timestamp_readable,
        'status': status,
        'transfer_count': transfer_count,
        'is_current': is_current
    }

handler = lambda_handler