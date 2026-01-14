import json
import urllib3
from datetime import datetime, timedelta

http = urllib3.PoolManager()

# Cache to avoid hitting rate limits (5 calls/minute)
price_cache = {
    'prices': {},
    'timestamp': None
}

def lambda_handler(event, context):
    try:
        # Check cache (refresh every 4 hours)
        if price_cache['timestamp']:
            cache_age = datetime.now() - price_cache['timestamp']
            if cache_age < timedelta(hours=4) and price_cache['prices']:
                print("Returning cached prices")
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'prices': price_cache['prices'],
                        'cached': True,
                        'cache_age_minutes': int(cache_age.total_seconds() / 60)
                    })
                }
        
        # Alpha Vantage API key
        api_key = 'YYWRS5AYR8G1S7VH'
        
        prices = {}
        errors = []
        
        # Fetch Corn price
        try:
            print("Fetching corn price...")
            corn_url = f'https://www.alphavantage.co/query?function=CORN&apikey={api_key}'
            response = http.request('GET', corn_url, timeout=8.0)
            corn_data = json.loads(response.data.decode('utf-8'))
            print(f"Corn API response: {json.dumps(corn_data)[:200]}")
            
            # Check if we got valid data
            if 'data' in corn_data and len(corn_data['data']) > 0:
                # Get most recent price
                latest = corn_data['data'][0]
                prices['Corn'] = float(latest.get('value', 4.85))
                print(f"Corn price: ${prices['Corn']}")
            else:
                print(f"No corn data, using fallback")
                prices['Corn'] = 4.85
                errors.append("Corn: No data from API")
        except Exception as e:
            print(f"Error fetching corn: {e}")
            prices['Corn'] = 4.85
            errors.append(f"Corn: {str(e)}")
        
        # Fetch Wheat price
        try:
            print("Fetching wheat price...")
            wheat_url = f'https://www.alphavantage.co/query?function=WHEAT&apikey={api_key}'
            response = http.request('GET', wheat_url, timeout=8.0)
            wheat_data = json.loads(response.data.decode('utf-8'))
            print(f"Wheat API response: {json.dumps(wheat_data)[:200]}")
            
            if 'data' in wheat_data and len(wheat_data['data']) > 0:
                latest = wheat_data['data'][0]
                prices['Wheat'] = float(latest.get('value', 6.25))
                print(f"Wheat price: ${prices['Wheat']}")
            else:
                print(f"No wheat data, using fallback")
                prices['Wheat'] = 6.25
                errors.append("Wheat: No data from API")
        except Exception as e:
            print(f"Error fetching wheat: {e}")
            prices['Wheat'] = 6.25
            errors.append(f"Wheat: {str(e)}")
        
        # Update cache
        price_cache['prices'] = prices
        price_cache['timestamp'] = datetime.now()
        
        response_data = {
            'prices': prices,
            'cached': False,
            'timestamp': datetime.now().isoformat(),
            'source': 'Alpha Vantage Commodities API'
        }
        
        if errors:
            response_data['errors'] = errors
            response_data['note'] = 'Some prices are fallback values due to API errors'
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as ex:
        print(f"Critical error: {str(ex)}")
        
        # Always return fallback prices on error
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'prices': {
                    'Corn': 4.85,
                    'Wheat': 6.25
                },
                'cached': False,
                'error': str(ex),
                'source': 'Fallback prices (API failed)'
            })
        }