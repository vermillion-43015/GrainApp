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

def lambda_handler(event, context):
    try:
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
        
        # Find chain heads that are ForSale
        for_sale = []
        for initial_hash, records in chains.items():
            # Sort by TransferCount DESC to get head
            records.sort(key=lambda x: int(x.get('TransferCount', 0)), reverse=True)
            head = records[0]
            
            if head.get('Status') == 'ForSale':
                for_sale.append(head)
        
        print(f"ForSale chain heads: {len(for_sale)}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            'body': json.dumps({
                'items': for_sale,
                'count': len(for_sale)
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