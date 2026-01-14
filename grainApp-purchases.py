import json,boto3
from decimal import Decimal
class DE(json.JSONEncoder):
    def default(self,o):return float(o)if isinstance(o,Decimal)else super().default(o)
def handler(e,c):
    em=e.get('requestContext',{}).get('authorizer',{}).get('claims',{}).get('email','')
    t=boto3.resource('dynamodb').Table('GrainTitles')
    r=t.query(IndexName='BuyerIndex',KeyConditionExpression='BuyerId=:v',ExpressionAttributeValues={':v':em})
    return{'statusCode':200,'headers':{'Content-Type':'application/json'},'body':json.dumps({'count':len(r.get('Items',[])),'items':r.get('Items',[])},cls=DE)}
