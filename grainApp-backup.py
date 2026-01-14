import json,boto3,os
from datetime import datetime
from decimal import Decimal
class DE(json.JSONEncoder):
    def default(self,o):return float(o)if isinstance(o,Decimal)else super().default(o)
def handler(e,c):
    i=boto3.resource('dynamodb').Table('GrainTitles').scan().get('Items',[])
    f=f"backup-{datetime.now().strftime('%Y%m%d')}.json"
    boto3.client('s3').put_object(Bucket=os.environ['BUCKET'],Key=f,Body=json.dumps(i,cls=DE).encode())
    return{'statusCode':200,'body':f'Backed up {len(i)} items'}
