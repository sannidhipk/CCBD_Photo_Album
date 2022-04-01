import json
import urllib.parse
import boto3
import datetime

import urllib3

host = 'https://search-photos-6rwd66icxrrlgk2nbw3vo2xqwm.us-west-2.es.amazonaws.com' # the OpenSearch Service domain, with https://
index = 'photos'
type = 'photo'
url = host + '/' + index + '/' + type + '/'
master_username= "sannidhi"
master_password= "Sannidhi123@"

headers = { "Content-Type": "application/json" }

def lambda_handler(event, context):
    # TODO implement
    print("query: " + str(event["queryStringParameters"]["q"]))
    
    client = boto3.client('lex-runtime')
    
    response = client.post_text(
        botName='myphotosbot',
        botAlias='dev',
        userId='ZZZJVTRWKA',
        inputText=event["queryStringParameters"]["q"]
    )
    
    if "slots" not in response:
        return {
        'statusCode': 200,
        'headers': {
                "Access-Control-Allow-Origin": "*",
                'Content-Type': 'application/json'
            },
        'body': "Incorrect query"
    }
    print(response["slots"])
    
    http = urllib3.PoolManager()
    url = "%s/%s/%s/_search?" % (host, index, type)
    headers = urllib3.make_headers(basic_auth='%s:%s' % (master_username, master_password))
    headers.update({
        'Content-Type': 'application/json',
        "Accept": "application/json"
    })
    query = {
              "query": {
                  "query_string": {
                        "query": f"(labels:{response['slots']['first_keyword']} OR labels:{response['slots']['second_keyword']})"
                    }
                }
            }
    response = http.request('GET', url, headers=headers, body=json.dumps(query))
    status = response.status
    print(response.data)
    data = json.loads(response.data)
    print("ES Response: [%s] %s" % (status, data))
    
    images = []
    for photo in data["hits"]["hits"]:
        print(photo['_source']['objectKey'])
        images.append({'image-url':'https://photos-bucket-s3.s3.amazonaws.com/' + photo['_source']['objectKey']})

    if not images:
        images = "No images exist for this query."
        
    
    print(images)    
    
    return {
        'statusCode': 200,
        'headers': {
                "Access-Control-Allow-Origin": "*",
                'Content-Type': 'application/json'
            },
        'body': json.dumps(images)
    }

#this is a change we have made
