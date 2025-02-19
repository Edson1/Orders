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
    "enproceso": os.environ.get('ORDERSQUEUEINPROCESS_QUEUE_URL'), #"SQS_QUEUE_IN_PROCESS", 
    "completada": os.environ.get('ORDERSQUEUECOMPLETED_QUEUE_URL'), #"SQS_QUEUE_COMPLETED", 
    "cancelada": os.environ.get('ORDERSQUEUECANCELLED_QUEUE_URL') #"SQS_QUEUE_CANCELLED"
}

sqs = boto3.client('sqs', region_name=AWS_REGION)

def validate_input(body):
    required_fields = ["fecha_entrega", "estado", "descripcion"]
    
    # Verificar si el cuerpo es un diccionario válido
    if not isinstance(body, dict):
        return "Invalid request body JSON format"
    
    # Verificar que todos los campos requeridos existen 
    for field in required_fields:
        if field not in body  or  not isinstance(body[field], str):
            return f"Missing or invalid '{field}' in request body."

    # Validar fecha_entrega (ejemplo de formato YYYY-MM-DD)
    try:
        datetime.datetime.strptime(body['fecha_entrega'], "%d-%m-%Y")
    except ValueError:
        return "Invalid 'fecha_entrega' format. Expected DD-MM-YYYY"
    
    return "valid"

def OrderLambda(event, context):     

    body = json.loads(event['body'])

    # Validar input data
    message = validate_input(body)
    if message != "valid":
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Input Validation error', 'error': message})
        }   
    
    # requerir motivo de cancelacion de orden
    if body['estado'].lower() == "cancelada":
        if len(body["descripcion"]) < 1:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Agregar el motivo de cancelacion de la Orden en la Descripcion, por favor'})
            }

    # Determinar si se genera un nuevo orderId o se usa el proporcionado
    if body["estado"].lower() == "recibida":
        orderId = str(uuid.uuid4())  # Generar un nuevo ID solo para "recibida"
    else:
        if "id" not in body or not body["id"]:  # Si no proporciona id, error
            return {
                    'statusCode': 400,
                    'body': json.dumps({'message': 'El campo id es obligatorio para actualizar una orden existente'})
            }
        orderId = body["id"]  # Usar el ID proporcionado por el frontend

    # print('Order ID: ' + orderId)

    try:
        order = {
            'id': orderId,
            'fecha_registro': datetime.datetime.now().isoformat(),
            'timestamp':  str(datetime.datetime.now().timestamp()),
            'descripcion': body['descripcion'],
            'fecha_entrega': body['fecha_entrega'],
            'estado': body['estado']
        }

        # Operación en DynamoDB
        table = dynamodb.Table(DYNAMODB_TABLE)

        if body["estado"].lower() == "recibida":
            # Insertar nueva orden
            table.put_item(Item=order)
        else:
            table.update_item(
                Key={'id': orderId},
                UpdateExpression="SET fecha_registro = :fecha_registro, "
                                "timestamp = :timestamp, "
                                "descripcion = :descripcion, "
                                "fecha_entrega = :fecha_entrega, "
                                "estado = :estado",
                ExpressionAttributeValues={
                    ':fecha_registro': order['fecha_registro'],
                    ':timestamp': order['timestamp'],
                    ':descripcion': order['descripcion'],
                    ':fecha_entrega': order['fecha_entrega'],
                    ':estado': order['estado']
                },
                ConditionExpression="attribute_exists(id)"  # Asegura que la orden ya existe antes de actualizar
            )
                
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
    
