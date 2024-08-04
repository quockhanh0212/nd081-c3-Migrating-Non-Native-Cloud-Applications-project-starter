import logging
import azure.functions as func
import psycopg2
import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def main(msg: func.ServiceBusMessage):
    notification_id = int(msg.get_body().decode('utf-8'))
    logging.info('Python ServiceBus queue trigger processed message: %s',notification_id)
    conn = psycopg2.connect("dbname=techconfdb user=postgres@postgres-sql-server password=Dummypass123 host=postgres-sql-server.postgres.database.azure.com")
    cur = conn.cursor()
    try:
        # TODO: Get notification message and subject from database using the notification_id
        cur.execute(f"SELECT message, subject FROM notification where id = {notification_id};")
        notification = cur.fetchone()
        notification_message = notification[0]
        notification_subject = notification[1]
        logging.info("notification: %s",notification_message)
        # TODO: Get attendees email and name
        cur.execute(f"SELECT email, first_name FROM attendee;")
        attendees = cur.fetchall()

        # TODO: Loop through each attendee and send an email with a personalized subject
        for attendee in attendees:
            attendee_email = attendee[0]
            attendee_first_name = attendee[1]
            subject = f"{attendee_first_name}: {notification_subject}"
            send_email(attendee_email, subject, notification_message)

        notification_completed_date = datetime.utcnow()
        notification_status = 'Notified {} attendees'.format(len(attendees))

        # TODO: Update the notification table by setting the completed date and updating the status with the total number of attendees notified
        cur.execute(f"UPDATE notification SET status = '{notification_status}', completed_date = '{notification_completed_date}' WHERE id = {notification_id};")    
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
    finally:
        cur.close()
        conn.close()

def send_email(email, subject, body):
    message = Mail(
        from_email='sendgridburner@gmail.com',
        to_emails=email,
        subject=subject,
        plain_text_content=body)

    sg = SendGridAPIClient('sendGridAPIKey')
    sg.send(message)