import boto3
import json


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('websiteTable-iac')

def lambda_handler(event, context):

    response = table.get_item(Key={'id':'0001'})

    try:
        countValue=response['Item']['visitorCounter']
    
    except:
        table.put_item(Item={
            'id':'0001',
            'visitorCounter': 1
        })
        updateCount = 1
    
    else:
        updateCount = countValue + 1
        table.update_item(Key={'id':'0001'},
        UpdateExpression='SET visitorCounter = :val1',
        ExpressionAttributeValues={':val1': updateCount})
    
    return {
        "statusCode": 200,
        "body": json.dumps({"value": int(updateCount)})
    }
