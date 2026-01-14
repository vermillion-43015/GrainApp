import json,boto3
from decimal import Decimal
class DE(json.JSONEncoder):
    def default(self,o):return float(o)if isinstance(o,Decimal)else super().default(o)
def handler(e,c):
    t=boto3.resource('dynamodb').Table('GrainTitles')
    r=t.query(IndexName='StatusIndex',KeyConditionExpression='#s=:v',ExpressionAttributeNames={'#s':'Status'},ExpressionAttributeValues={':v':'InRoute'})
    return{'statusCode':200,'headers':{'Content-Type':'application/json'},'body':json.dumps({'count':len(r.get('Items',[])),'items':r.get('Items',[])},cls=DE)}
