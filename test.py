import unittest
import json
#import uuid
#import datetime
from unittest.mock import patch, MagicMock

from handler import OrderLambda  

class TestOrderLambda(unittest.TestCase):

    @patch('handler.dynamodb')
    @patch('handler.sqs')
    def test_successful_order_creation(self, mock_sqs, mock_dynamodb):
        """Test: successful order creation"""

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        mock_sqs_client = MagicMock()
        mock_sqs.send_message = mock_sqs_client.send_message

        event = {
            "body": json.dumps({
                "descripcion": "Test Order",
                "fecha_entrega": "2025-12-31",
                "estado": "enproceso"
            })
        }
        response = OrderLambda(event, None)

        self.assertEqual(response["statusCode"], 201)
        self.assertIn("Orden registrada con exito", response["body"])

        # Verify order was inserted into DynamoDB
        mock_table.put_item.assert_called_once()

    def test_missing_input_data(self):
        """Test: order creation fails when mandatory input data is missing"""

        event = {
            "body": json.dumps({
                'fecha_entrega': "",
                "descripcion": "Test Order",
                "estado": "recibida"
            })
        }
        response = OrderLambda(event, None)

        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Missing input data, please verify the request body", response["body"])

    def test_cancelled_order_without_description(self):
        """Test: order fails when 'estado' is 'cancelada' but missing motivo in 'descripcion'"""

        event = {
            "body": json.dumps({
                "descripcion": "",
                "fecha_entrega": "2025-12-31",
                "estado": "cancelada"
            })
        }
        response = OrderLambda(event, None)

        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Agregar el motivo de cancelacion de la Orden en la Descripcion, por favor", response["body"])

    @patch('handler.dynamodb')
    def test_dynamodb_put_data_failure(self, mock_dynamodb):
        """Test: failure when DynamoDB insert fails"""

        mock_table = MagicMock()
        mock_table.put_item.side_effect = Exception("DynamoDB failure")
        mock_dynamodb.Table.return_value = mock_table

        event = {
            "body": json.dumps({
                "descripcion": "Test Order",
                "fecha_entrega": "2025-12-31",
                "estado": "recibida"
            })
        }
        response = OrderLambda(event, None)

        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Error al procesar la orden", response["body"])

if __name__ == "__main__":
    unittest.main()