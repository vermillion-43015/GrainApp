import json
import boto3
import hashlib
from datetime import datetime
from decimal import Decimal

def handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        hashes = body.get('hashes', [])
        buyer_name = body.get('buyer_name', '')
        
        if not hashes or not buyer_name:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Missing hashes or buyer_name'})
            }
        
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('GrainTitles')
        
        updated_count = 0
        errors = []
        
        for title_hash in hashes:
            try:
                # Get the current item
                response = table.get_item(Key={'TitleHash': title_hash})
                
                if 'Item' not in response:
                    errors.append(f"Item with hash {title_hash} not found")
                    continue
                
                item = response['Item']
                
                # Generate new final title hash
                timestamp = int(datetime.now().timestamp())
                hash_data = f"{item['TitleHash']}{item['PreviousHash']}{buyer_name}{timestamp}"
                final_title_hash = hashlib.sha256(hash_data.encode()).hexdigest()
                
                # Update the item
                table.update_item(
                    Key={'TitleHash': title_hash},
                    UpdateExpression='SET #status = :status, BuyerName = :buyer_name, BuyerId = :buyer_id, FinalTitleHash = :final_hash, #ts = :timestamp',
                    ExpressionAttributeNames={
                        '#status': 'Status',
                        '#ts': 'Timestamp'
                    },
                    ExpressionAttributeValues={
                        ':status': 'TitleIssued',
                        ':buyer_name': buyer_name,
                        ':buyer_id': 'B001',
                        ':final_hash': final_title_hash,
                        ':timestamp': timestamp,
                        ':old_status': 'ForSale'
                    },
                    ConditionExpression='#status = :old_status'
                )
                
                updated_count += 1
                
            except Exception as ex:
                errors.append(f"Error updating {title_hash}: {str(ex)}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'updated': updated_count,
                'errors': errors
            })
        }
        
    except Exception as ex:
        print(f"Error: {str(ex)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(ex),
                'type': type(ex).__name__
            })
        }