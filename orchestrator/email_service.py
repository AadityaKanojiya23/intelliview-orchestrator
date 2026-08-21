"""
Email Notification Service using smtplib.
Sends email notifications for scheduled interviews and other events.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP using smtplib."""

    def __init__(self):
        self.settings = get_settings()

    def send_interview_confirmation(
        self,
        candidate_name: str,
        candidate_email: str,
        interview_date: str,
        interview_time: str,
        interviewer_name: str,
        schedule_id: str,
        notes: str | None = None,
    ) -> tuple[bool, str]:
        """
        Send a confirmation email for a scheduled interview using smtplib.

        Args:
            candidate_name: Name of the candidate
            candidate_email: Email address of the candidate
            interview_date: Date string (e.g., "2026-08-12")
            interview_time: Time string (e.g., "10:00 AM UTC")
            interviewer_name: Name/ID of the assigned interviewer
            schedule_id: Unique schedule ID
            notes: Optional additional notes

        Returns:
            tuple[bool, str]: (Success boolean, Status/error message string)
        """
        sender_email = self.settings.smtp_from_email or "notifications@intelliview.ai"
        host = self.settings.smtp_host or "localhost"
        port = self.settings.smtp_port or 1025

        subject = f"Interview Scheduled: AI Interview Session ({interview_date})"

        # Plain text fallback
        text_body = f"""Dear {candidate_name},

Your interview has been successfully scheduled!

Interview Details:
------------------
Schedule ID: {schedule_id}
Candidate: {candidate_name} ({candidate_email})
Date: {interview_date}
Time: {interview_time}
Interviewer: {interviewer_name}
{f"Notes: {notes}" if notes else ""}

Please make sure to join on time. 

Best regards,
IntelliView Interview Team
"""

        # HTML Email format
        html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #09090b; color: #f4f4f5; margin: 0; padding: 20px; }}
    .card {{ max-width: 600px; margin: 0 auto; background-color: #18181b; border: 1px solid #27272a; border-radius: 12px; padding: 28px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
    .header {{ border-bottom: 1px solid #27272a; padding-bottom: 16px; margin-bottom: 20px; }}
    .header h2 {{ color: #6366f1; margin: 0; font-size: 22px; }}
    .detail-row {{ display: flex; margin-bottom: 12px; font-size: 15px; }}
    .label {{ font-weight: 600; color: #a1a1aa; width: 140px; shrink: 0; }}
    .value {{ color: #f4f4f5; font-weight: 500; }}
    .badge {{ display: inline-block; background-color: rgba(99, 102, 241, 0.15); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.3); padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: 600; }}
    .footer {{ margin-top: 24px; border-top: 1px solid #27272a; padding-top: 16px; font-size: 12px; color: #71717a; text-align: center; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h2>🎉 Interview Confirmation</h2>
      <p style="color: #a1a1aa; font-size: 14px; margin-top: 4px;">Your AI technical interview has been scheduled.</p>
    </div>

    <p style="font-size: 15px;">Dear <strong>{candidate_name}</strong>,</p>
    <p style="font-size: 14px; color: #d4d4d8;">We are pleased to invite you to your upcoming technical interview session. Below are the details:</p>

    <div style="background-color: #27272a; border-radius: 8px; padding: 16px; margin: 20px 0;">
      <table style="width: 100%; border-collapse: collapse;">
        <tr>
          <td style="padding: 6px 0; color: #a1a1aa; font-size: 14px; width: 130px;">Schedule ID:</td>
          <td style="padding: 6px 0; color: #f4f4f5; font-size: 14px; font-family: monospace;">{schedule_id}</td>
        </tr>
        <tr>
          <td style="padding: 6px 0; color: #a1a1aa; font-size: 14px;">Candidate:</td>
          <td style="padding: 6px 0; color: #f4f4f5; font-size: 14px;"><strong>{candidate_name}</strong> ({candidate_email})</td>
        </tr>
        <tr>
          <td style="padding: 6px 0; color: #a1a1aa; font-size: 14px;">Date:</td>
          <td style="padding: 6px 0; color: #38bdf8; font-size: 14px; font-weight: 600;">{interview_date}</td>
        </tr>
        <tr>
          <td style="padding: 6px 0; color: #a1a1aa; font-size: 14px;">Time:</td>
          <td style="padding: 6px 0; color: #38bdf8; font-size: 14px; font-weight: 600;">{interview_time}</td>
        </tr>
        <tr>
          <td style="padding: 6px 0; color: #a1a1aa; font-size: 14px;">Interviewer:</td>
          <td style="padding: 6px 0; color: #f4f4f5; font-size: 14px;">{interviewer_name}</td>
        </tr>
        {f'<tr><td style="padding: 6px 0; color: #a1a1aa; font-size: 14px;">Notes:</td><td style="padding: 6px 0; color: #e4e4e7; font-size: 14px;">{notes}</td></tr>' if notes else ""}
      </table>
    </div>

    <p style="font-size: 14px; color: #a1a1aa;">Please ensure your camera and microphone are ready prior to the interview time.</p>

    <div class="footer">
      IntelliView AI Interview Platform &bull; Automated Notification
    </div>
  </div>
</body>
</html>
"""

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = candidate_email

        message.attach(MIMEText(text_body, "plain"))
        message.attach(MIMEText(html_body, "html"))

        try:
            logger.info(
                f"Attempting to send email via SMTP to {candidate_email} via {host}:{port}"
            )
            with smtplib.SMTP(host=host, port=port, timeout=10) as server:
                if self.settings.smtp_use_tls:
                    server.starttls()
                if self.settings.smtp_user and self.settings.smtp_password:
                    server.login(self.settings.smtp_user, self.settings.smtp_password)
                server.send_message(message)

            logger.info(f"Email notification successfully sent to {candidate_email}")
            return True, "Email sent successfully"

        except Exception as e:
            error_msg = f"Failed to send email notification to {candidate_email}: {e!s}"
            logger.warning(error_msg)
            return False, error_msg


# Default instance
email_service = EmailService()
