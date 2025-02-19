import json
import boto3
import os
import datetime
import uuid

# Inicializar servicios de AWS
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
DYNAMODB_TABLE = os.environ.get('ORDERSTABLE_TABLE_ARN')

dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

SQS_QUEUES = {
    "recibida": os.environ.get('ORDERSQUEUERECEIVED_QUEUE_URL'), #"SQS_QUEUE_RECEIVED",    
    "enproceso": os.environ.get('ORDERSQUEUEINPROCESS_QUEUE_URL'), #"SQS_QUEUE_IN_PROCESS", ###URL
    "completada": os.environ.get('ORDERSQUEUECOMPLETED_QUEUE_URL'), #"SQS_QUEUE_COMPLETED", #### os.environ.get('SQS_QUEUE_IN_PROCESS')
    "cancelada": os.environ.get('ORDERSQUEUECANCELLED_QUEUE_URL') #"SQS_QUEUE_CANCELLED"
}

sqs = boto3.client('sqs', region_name=AWS_REGION)

def OrderLambda(event, context):

    # parse json data
    body = json.loads(event['body'])
    
    # verify post variables
    validateBody = body["fecha_entrega"]

    if len(validateBody) < 1:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Missing input data, please verify the request body'})
        }
    
    # requerir motivo de cancelacion de orden
    if body['estado'].lower() == "cancelada":
        if len(body["descripcion"]) < 1:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Agregar el motivo de cancelacion de la Orden en la Descripcion, por favor'})
            }

    orderId = uuid.uuid4()
    print('Order ID: ' + str(orderId))

    try:
        order = {
            'id': str(orderId),
            'fecha_registro': datetime.datetime.now().isoformat(),
            'timestamp':  str(datetime.datetime.now().timestamp()),
            'descripcion': body['descripcion'],
            'fecha_entrega': body['fecha_entrega'],
            'estado': body['estado']
        }

        # Guardar en DynamoDB
        table = dynamodb.Table(DYNAMODB_TABLE)
        table.put_item(Item=order)
                
        # Enviar order a SQS según estado
        queue_url = SQS_QUEUES.get(order['estado'].lower())
        if queue_url:
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(order),
                MessageGroupId="1"
            )

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Orden registrada con exito', 'order': order})
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Error al procesar la orden', 'error': str(e)})
        }
    


