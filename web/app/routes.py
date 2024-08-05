from flask import render_template, request, redirect, flash, session
from app import app, db, servicebus_client
from azure.servicebus import ServiceBusMessage
from datetime import datetime
import logging
from app.models import Attendee, Notification

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/Registration', methods=['POST', 'GET'])
def registration():
    if request.method == 'POST':
        attendee = Attendee(
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            email=request.form['email'],
            job_position=request.form['job_position'],
            company=request.form['company'],
            city=request.form['city'],
            state=request.form['state'],
            interests=request.form['interest'],
            comments=request.form['message'],
            conference_id=app.config.get('CONFERENCE_ID')
        )

        try:
            db.session.add(attendee)
            db.session.commit()
            session['message'] = 'Thank you, {} {}, for registering!'.format(attendee.first_name, attendee.last_name)
            return redirect('/Registration')
        except Exception as e:
            logging.error('Error occurred while saving your information: {}'.format(e))
            flash('An error occurred while processing your request.', 'error')
            return redirect('/Registration')

    else:
        if 'message' in session:
            message = session.pop('message', None)
            return render_template('registration.html', message=message)
        return render_template('registration.html')

@app.route('/Attendees')
def attendees():
    attendees = Attendee.query.order_by(Attendee.submitted_date).all()
    return render_template('attendees.html', attendees=attendees)

@app.route('/Notifications')
def notifications():
    notifications = Notification.query.order_by(Notification.id).all()
    return render_template('notifications.html', notifications=notifications)

@app.route('/Notification', methods=['POST', 'GET'])
def notification():
    if request.method == 'POST':
        notification = Notification()
        notification.message = request.form['message']
        notification.subject = request.form['subject']
        notification.status = 'Notifications submitted'
        notification.submitted_date = datetime.utcnow()

        try:
            db.session.add(notification)
            db.session.commit()

            # Send message to the queue
            with servicebus_client:
                sender = servicebus_client.get_queue_sender(queue_name=app.config.get('SERVICE_BUS_QUEUE_NAME'))
                with sender:
                    msg = ServiceBusMessage(str(notification.id))
                    sender.send_messages(msg)

            # Update notification status to include the number of attendees notified
            attendees_count = Attendee.query.count()
            notification.status = f'Notified {attendees_count} attendees'
            notification.completed_date = datetime.utcnow()
            db.session.commit()

            return redirect('/Notifications')
        except Exception as e:
            logging.error('Unable to save notification: {}'.format(e))
            flash('An error occurred while processing your request.', 'error')
            return redirect('/Notification')
    return render_template('notification.html')

# def send_email(email, subject, body):
#     if app.config.get('SENDGRID_API_KEY'):
#         message = Mail(
#             from_email=app.config.get('ADMIN_EMAIL_ADDRESS'),
#             to_emails=email,
#             subject=subject,
#             plain_text_content=body
#         )

#         sg = SendGridAPIClient(app.config.get('SENDGRID_API_KEY'))
#         sg.send(message)