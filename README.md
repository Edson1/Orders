# Orders
Microservicio de ordenes de trabajo

## cómo crear IaaC del proyecto en cloud AWS desde CloudFormation:
Importat en CloudFormation el serverless.yml , que creara una AWS APIGateway conectada a la funcion AWS Lambda que procesa las órdenes de trabajo, con DynamoDB como base de datos NoSQL, y SQS para la gestión de colas. Ver diagrama de arquitectura Amazon Web Services (AWS) adjunto en este repositorio.

El servicio recibe órdenes de trabajo a través de una API REST (API Gateway), almacena las órdenes en DynamoDB con los atributos requeridos, y publicar mensajes en las colas SQS dependiendo del estado de la orden.

Se definen las policies necesarias para que la función Lambda pueda interactuar con DynamoDB (operaciones CRUD) y SQS, ademas tiene permisos para permitir el acceso a la funcion a traves de una API gateway.

El Codigo python (handler.py) de la lambda esta almacenado en un bucket S3 con acceso publico: https://publicrepos.s3.us-west-2.amazonaws.com/handler.zip

## Test microservice using an open url. 
POST https://dvlkefayse.execute-api.us-west-2.amazonaws.com/Dev/orders
Input body example:
{
        "fecha_entrega": "10/04/2026",
        "descripcion": "creacion de orden de trabajo",
        "estado": "enproceso"
}

## example Output:
OK status 200
{
    "message": "Orden registrada con exito",
    "order": {
        "id": "95205688-9a6f-4f3b-9e03-787792cf8338",
        "fecha_registro": "2025-02-19T01:24:06.559861",
        "timestamp": "1739928246.559875",
        "descripcion": "creacion de orden de trabajo",
        "fecha_entrega": "10/04/2026",
        "estado": "recibida"
    }
}

## Decisiones técnicas:
La API esta configurada para accesos desde cualquier origen (CORS) para facilitar las pruebas iniciales, igualmente tampoco requiere API keys o algun otro tipo de autorizacion como tokens que obviamente se requieren para mantener la seguridad del microservicio.
Utilicé una cola SQS para cada estado, aunque creo que tambien se puede hacer con una sola cola y usar 4 group Ids diferentes para mantener separadas las ordenes dentro de una unica cola SQS.


## Cómo escalaría esta solución para manejar un alto volumen de solicitudes.

## Cambios que implementaría en la solución propuesta para procesar las órdenes en el mismo orden en que fueron recibidas.
Las colas SQS estan configuradas con el algoritmo FIFO para procesarlas en el mismo orden en que fueron recibidas, y tambien coloqué un timestamp que luego puede ser usada como sort key para realizar el ordenamiento si es necesario

## Ejecutar pruebas unitarias de la funcion lambda con:
pip install boto3 moto
python -m unittest test.py

