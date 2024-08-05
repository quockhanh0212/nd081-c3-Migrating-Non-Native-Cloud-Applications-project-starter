import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from azure.servicebus import ServiceBusClient, ServiceBusMessage, TransportType
import logging

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')

app.secret_key = app.config.get('SECRET_KEY')

# Initialize the database
db = SQLAlchemy(app)

# Configure logging
logging.basicConfig(level=logging.ERROR)

# Configure the Service Bus Client
servicebus_client = None
try:
    servicebus_client = ServiceBusClient.from_connection_string(
        app.config.get('SERVICE_BUS_CONNECTION_STRING'),
        transport_type=TransportType.AmqpOverWebsocket  # Use TransportType here
    )

    # Test connection by sending a test message
    with servicebus_client:
        sender = servicebus_client.get_queue_sender(queue_name=app.config.get('SERVICE_BUS_QUEUE_NAME'))
        with sender:
            test_message = ServiceBusMessage("Test message to check queue connection")
            sender.send_messages(test_message)
            logging.info("Successfully connected to the Azure Service Bus Queue and sent a test message.")

except Exception as e:
    logging.error(f"Failed to create Service Bus client or send test message: {e}")

# Import routes at the end to avoid circular imports
from . import routes

if __name__ == "__main__":
    app.run(debug=True)
