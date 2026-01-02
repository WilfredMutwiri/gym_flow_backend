from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
import os

logger = logging.getLogger(__name__)

def send_notification_email(notification):
    """
    Send an email for a notification.
    """
    try:
        user = notification.recipient
        if not user.email:
            logger.warning(f"User {user.id} has no email address. Skipping notification email.")
            return False

        subject = f"FitHub Notification: {notification.title}"
        
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
        dashboard_url = f"{frontend_url}/dashboard"
        
        # Simple HTML content
        html_message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8fafc; padding: 20px; text-align: center;">
                <h2 style="color: #0f172a;">FitHub</h2>
            </div>
            <div style="padding: 20px; border: 1px solid #e2e8f0;">
                <h3 style="color: #334155;">{notification.title}</h3>
                <p style="color: #475569; font-size: 16px; line-height: 1.5;">{notification.message}</p>
                <div style="margin-top: 30px; text-align: center;">
                    <a href="{dashboard_url}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Go to Dashboard</a>
                </div>
            </div>
            <div style="padding: 20px; text-align: center; color: #94a3b8; font-size: 12px;">
                <p>&copy; 2024 FitHub. All rights reserved.</p>
                <p>You received this email because you have notifications enabled on your account.</p>
            </div>
        </div>
        """
        
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        notification.email_sent = True
        notification.save()
        return True
        
    except Exception as e:
        logger.error(f"Failed to send notification email to {notification.recipient.email}: {str(e)}")
        return False
