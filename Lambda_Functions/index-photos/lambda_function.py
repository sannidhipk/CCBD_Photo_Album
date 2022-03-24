import json
import urllib.parse
import boto3
import datetime

import urllib3


# region = 'us-west-2' # e.g. us-east-1
# service = 'es'
# credentials = boto3.Session().get_credentials()
# awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

host = 'https://search-photos-6rwd66icxrrlgk2nbw3vo2xqwm.us-west-2.es.amazonaws.com' # the OpenSearch Service domain, with https://
index = 'photos'
types = 'photo'
url = host + '/' + index + '/' + types + '/'
master_username= "sannidhi"
master_password= "Sannidhi123@"

headers = { "Content-Type": "application/json" }

s3 = boto3.client('s3')
def lambda_handler(event, context):
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    # try:
    #     response = s3.get_object(Bucket=bucket, Key=key)
    #     print("CONTENT TYPE: " + response['ContentType'])
    #     # return response['ContentType']
    # except Exception as e:
    #     print(e)
    #     print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
    #     raise e
    client = boto3.client('rekognition')
    
    response = client.detect_labels(
        Image={
            'S3Object': {
                'Bucket': bucket,
                'Name': key,
            }
        },
        MaxLabels=50,
        MinConfidence=0.98
    )
    labels = set()
    for label in response['Labels']:
        labels.add(label['Name'].lower())
    # print("labels are: " + str(labels))
    
    response = s3.head_object(
        Bucket=bucket,
        Key=key,
    )
    if "Metadata" in response and "customlabels" in response["Metadata"]:
        labels = labels | set(response["Metadata"]['customlabels'].lower().split(", "))
    
    print("all labels: " + str(labels))
    # print(response['Metadata']["customlabels"])
    
    #Store json in opensearch
    opensearch_js = {"objectKey": key, 
                    "bucket": bucket,
                    "createdTimestamp": str(datetime.datetime.now().strftime("%Y-%m-%d"'T'"%H:%M:%S")),
                    "labels": list(labels)
    }
    
    print(opensearch_js)
    
    # r = urllib3.request.put(url + id,json=opensearch_js, headers=headers)
        

    http = urllib3.PoolManager()
    url = "%s/%s/%s/" % (host, index, types)
    print(url)
    headers = urllib3.make_headers(basic_auth='%s:%s' % (master_username, master_password))
    headers.update({
        'Content-Type': 'application/json',
        "Accept": "application/json"
    })
    payload = opensearch_js
    response = http.request('POST', url, headers=headers, body=json.dumps(payload))
    status = response.status
    data = json.loads(response.data)
    print("ES Response: [%s] %s" % (status, data))

    return {
        'statusCode': response.status,
        'body': json.loads(response.data)
    }
