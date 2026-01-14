import json
import boto3
import hashlib

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('GrainTitles')

def validate_single_record(item):
    """Validate a single record's hash"""
    grain = item['GrainType']
    qty = int(item['Quantity'])
    price = item['PriceString']
    transfer_count = int(item.get('TransferCount', 0))
    relist_count = int(item.get('RelistCount', 0))
    stored_hash = item['CurrentHash']
    seller_id = item.get('SellerID', '')
    status = item.get('Status', '')
    
    if transfer_count == 0 and relist_count == 0:
        # Original creation hash format:
        # hash_input = f"{grain_type}{quantity}{seller_id}{price_string}{timestamp}"
        timestamp = item.get('HashTimestamp') or item.get('TimestampISO')
        hash_input = f"{grain}{qty}{seller_id}{price}{timestamp}"
    elif relist_count > 0 and status == 'ForSale':
        # Relist hash format:
        # hash_input = f"{previous_hash}{grain_type}{quantity}{owner_id}{price}{timestamp_iso}{transfer_count}R{relist_count}"
        prev = item.get('PreviousHash', '')
        timestamp = item.get('HashTimestamp') or item.get('RelistedAtISO', '')
        hash_input = f"{prev}{grain}{qty}{seller_id}{price}{timestamp}{transfer_count}R{relist_count}"
    else:
        # Transfer hash format - SellerID is the buyer who just received this
        # hash_input = f"{previous_hash}{grain_type}{quantity}{buyer_id}{price}{timestamp_iso}{transfer_count}"
        prev = item.get('PreviousHash', '')
        timestamp = item.get('LastTransferTimestampISO') or item.get('HashTimestamp', '')
        hash_input = f"{prev}{grain}{qty}{seller_id}{price}{timestamp}{transfer_count}"
    
    calculated_hash = hashlib.sha256(hash_input.encode()).hexdigest()
    
    print(f"Transfer #{transfer_count}, Relist #{relist_count}, Status: {status}:")
    print(f"  Hash input: {hash_input}")
    print(f"  Calculated: {calculated_hash}")
    print(f"  Stored:     {stored_hash}")
    print(f"  Match: {calculated_hash == stored_hash}")
    
    return calculated_hash == stored_hash

def handler(event, context):
    try:
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', event)
        hash_to_validate = body.get('title_hash') or body.get('TitleHash')
        
        if not hash_to_validate:
            return {'statusCode': 400, 'body': json.dumps({'chain_valid': False})}
        
        # First try to find by TitleHash (primary key)
        response = table.get_item(Key={'TitleHash': hash_to_validate})
        
        if 'Item' not in response:
            # Maybe they sent CurrentHash - scan for it
            scan_response = table.scan(
                FilterExpression='CurrentHash = :hash',
                ExpressionAttributeValues={':hash': hash_to_validate}
            )
            items = scan_response.get('Items', [])
            if not items:
                return {'statusCode': 404, 'body': json.dumps({'chain_valid': False})}
            item = items[0]
        else:
            item = response['Item']
        
        # Validate this record
        is_valid = validate_single_record(item)
        
        print(f"Final result: {'VALID' if is_valid else 'INVALID'}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'chain_valid': is_valid,
                'isValid': is_valid,
                'validationStatus': 'Valid' if is_valid else 'Invalid'
            })
        }
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({'chain_valid': False})
        }

lambda_handler = handler