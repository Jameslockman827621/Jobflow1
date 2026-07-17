"""
Email Service

Supports:
- SendGrid (production)
- SMTP fallback
- Console output (development only — never success in production)
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from app.core.config import settings

logger = logging.getLogger(__name__)


def _is_production() -> bool:
    return str(settings.ENVIRONMENT).lower() == "production"


class EmailService:
    def __init__(self):
        # Use SendGrid if configured, otherwise SMTP
        self.sendgrid_api_key = settings.SENDGRID_API_KEY
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER or ""
        self.smtp_password = settings.SMTP_PASSWORD or ""
        self.from_email = settings.FROM_EMAIL
        self.from_name = "JobScale"

    def _unsub_footer(self, user_id: Optional[int] = None) -> str:
        manage = f"{settings.APP_URL.rstrip('/')}/alerts"
        if user_id:
            from app.services.unsubscribe import unsubscribe_url

            unsub = unsubscribe_url(user_id)
        else:
            unsub = manage
        return (
            f'<p style="color:#9ca3af;font-size:12px;margin-top:24px;text-align:center">'
            f'<a href="{manage}" style="color:#9ca3af">Manage preferences</a>'
            f' &nbsp;|&nbsp; '
            f'<a href="{unsub}" style="color:#9ca3af">Unsubscribe</a></p>'
        )
    
    def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send an email. Production never reports success for console-only fallback."""
        sg_key = (self.sendgrid_api_key or "").strip()
        if sg_key and sg_key.lower() not in ("mock", "placeholder", "your-key"):
            try:
                import httpx

                resp = httpx.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {sg_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "personalizations": [{"to": [{"email": to}]}],
                        "from": {"email": self.from_email, "name": self.from_name},
                        "subject": subject,
                        "content": [
                            {
                                "type": "text/plain",
                                "value": text_content
                                or __import__("re").sub(r"<[^>]+>", "", html_content),
                            },
                            {"type": "text/html", "value": html_content},
                        ],
                    },
                    timeout=20.0,
                )
                if resp.status_code in (200, 202):
                    return True
                logger.warning("SendGrid failed: %s %s", resp.status_code, resp.text[:300])
            except Exception as e:
                logger.warning("SendGrid error: %s", e)

        has_smtp = bool(self.smtp_user and self.smtp_password)
        if settings.DEBUG and not _is_production() and not has_smtp:
            print(f"\nEMAIL (DEV MODE — no SMTP/SendGrid)")
            print(f"To: {to}")
            print(f"Subject: {subject}")
            print(f"Content: {html_content[:200]}...")
            print()
            return True

        if not has_smtp and _is_production():
            logger.error("Email send failed: no SendGrid/SMTP configured in production")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to

            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            else:
                import re

                text = re.sub(r"<[^>]+>", "", html_content)
                msg.attach(MIMEText(text, "plain"))

            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            return True
        except Exception as e:
            logger.error("Failed to send email: %s", e)
            return False
    
    def send_welcome_email(self, to: str, name: str) -> bool:
        """Send welcome email after registration"""
        subject = "Welcome to JobScale! 🚀"
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>Welcome to JobScale, {name}!</h2>
            
            <p>You're now ready to supercharge your job search with AI.</p>
            
            <h3>Get Started:</h3>
            <ol>
                <li><strong>Complete your profile</strong> - Add your skills and preferences</li>
                <li><strong>Browse jobs</strong> - See AI-matched opportunities</li>
                <li><strong>Apply with AI</strong> - Let us tailor your CV and cover letter</li>
            </ol>
            
            <p style="margin-top: 30px;">
                <a href="{settings.APP_URL}/profile" 
                   style="background-color: #2563eb; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 6px; display: inline-block;">
                    Complete Your Profile
                </a>
            </p>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;" />
            
            <p style="color: #666; font-size: 14px;">
                Questions? Reply to this email - we read every message.
            </p>
            
            <p>
                Best,<br>
                The JobScale Team
            </p>
        </body>
        </html>
        """
        return self.send_email(to, subject, html)
    
    def send_application_confirmation(self, to: str, job_title: str, company: str) -> bool:
        """Send application confirmation"""
        subject = f"Application Submitted: {job_title} at {company}"
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>Application Submitted! ✓</h2>
            
            <p>Great news! Your application has been submitted for:</p>
            
            <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="font-size: 18px; font-weight: bold; margin: 0;">{job_title}</p>
                <p style="color: #666; margin: 5px 0 0 0;">{company}</p>
            </div>
            
            <h3>What's Next?</h3>
            <ol>
                <li><strong>Track your application</strong> - Check your dashboard for updates</li>
                <li><strong>Prepare for interviews</strong> - We'll send interview prep when you hear back</li>
                <li><strong>Keep applying</strong> - Don't put all your eggs in one basket!</li>
            </ol>
            
            <p style="margin-top: 30px;">
                <a href="{settings.APP_URL}/dashboard" 
                   style="background-color: #2563eb; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 6px; display: inline-block;">
                    View Your Applications
                </a>
            </p>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;" />
            
            <p style="color: #666; font-size: 14px;">
                Average response time: 5-7 business days. We'll notify you when you hear back!
            </p>
            
            <p>
                Good luck!<br>
                The JobScale Team
            </p>
        </body>
        </html>
        """
        return self.send_email(to, subject, html)
    
    def send_interview_notification(self, to: str, job_title: str, company: str, details: str) -> bool:
        """Send interview notification"""
        subject = f"🎉 Interview Request: {job_title} at {company}"
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #16a34a;">🎉 Great News!</h2>
            
            <p>You've been invited to interview for:</p>
            
            <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="font-size: 18px; font-weight: bold; margin: 0;">{job_title}</p>
                <p style="color: #666; margin: 5px 0 0 0;">{company}</p>
            </div>
            
            <h3>Interview Details:</h3>
            <div style="background: #fef3c7; padding: 15px; border-radius: 6px; border-left: 4px solid #f59e0b;">
                {details}
            </div>
            
            <h3>Prepare with JobScale:</h3>
            <ul>
                <li>Research the company</li>
                <li>Review common interview questions for this role</li>
                <li><a href="{settings.APP_URL.rstrip('/')}/interview-coach">Practice with the AI interview coach</a></li>
            </ul>
            
            <p style="margin-top: 30px;">
                <a href="{settings.APP_URL.rstrip('/')}/interview-coach" 
                   style="background-color: #16a34a; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 6px; display: inline-block;">
                    Open interview coach
                </a>
            </p>
            
            <p>
                You've got this! 💪<br>
                The JobScale Team
            </p>
        </body>
        </html>
        """
        return self.send_email(to, subject, html)
    
    def send_job_alert(self, to: str, jobs: List[dict], user_id: Optional[int] = None) -> bool:
        """Send job alert email with new matching jobs"""
        subject = f"{len(jobs)} New Jobs Match Your Profile"
        
        jobs_html = ""
        for job in jobs[:5]:  # Max 5 jobs
            jobs_html += f"""
            <div style="border: 1px solid #e5e7eb; padding: 15px; border-radius: 6px; margin-bottom: 15px;">
                <p style="font-weight: bold; margin: 0 0 5px 0;">{job['title']}</p>
                <p style="color: #666; margin: 0 0 5px 0;">{job['company']} • {job['location']}</p>
                <p style="margin: 0;">
                    <a href="{job['url']}" style="color: #2563eb;">View Job →</a>
                </p>
            </div>
            """
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>New Jobs for You!</h2>
            
            <p>We found {len(jobs)} new jobs that match your profile:</p>
            
            {jobs_html}
            
            <p style="margin-top: 30px;">
                <a href="{settings.APP_URL}/dashboard" 
                   style="background-color: #2563eb; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 6px; display: inline-block;">
                    See All Jobs
                </a>
            </p>
            
            {self._unsub_footer(user_id)}
            
            <p>
                The JobScale Team
            </p>
        </body>
        </html>
        """
        return self.send_email(to, subject, html)

    def send_salary_upgrade_alert(self, to: str, name: str, current_salary: int, jobs: List[dict], user_id: Optional[int] = None) -> bool:
        """Send salary upgrade alert - the post-hire retention email"""
        subject = f"💰 We found jobs paying more than your £{current_salary:,} salary"
        
        jobs_html = ""
        for job in jobs[:5]:
            increase = job.get('salary_increase', 0)
            jobs_html += f"""
            <div style="border: 1px solid #e5e7eb; padding: 15px; border-radius: 8px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <p style="font-weight: bold; margin: 0 0 4px 0; font-size: 15px;">{job['title']}</p>
                        <p style="color: #666; margin: 0; font-size: 13px;">{job['company']} • {job.get('location', '')}</p>
                    </div>
                    <div style="background: #dcfce7; color: #166534; padding: 6px 12px; border-radius: 20px; font-weight: 600; font-size: 13px; white-space: nowrap;">
                        +£{increase:,}
                    </div>
                </div>
                <p style="margin: 8px 0 0 0;">
                    <a href="{job.get('url', '#')}" style="color: #2563eb; font-size: 13px;">View & Apply →</a>
                </p>
            </div>
            """
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #059669, #10b981); color: white; padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">Salary Upgrade Found! 💰</h1>
                <p style="margin: 8px 0 0 0; opacity: 0.9;">Higher-paying opportunities matched to your profile</p>
            </div>
            
            <div style="padding: 25px; background: white; border: 1px solid #e5e7eb; border-top: none;">
                <p>Hi {name},</p>
                
                <p>Great news! We found <strong>{len(jobs)} jobs</strong> that pay more than your current salary of <strong>£{current_salary:,}</strong>:</p>
                
                {jobs_html}
                
                <p style="margin-top: 25px; text-align: center;">
                    <a href="{settings.APP_URL}/dashboard" 
                       style="background-color: #059669; color: white; padding: 14px 28px; 
                              text-decoration: none; border-radius: 8px; display: inline-block; font-weight: 600;">
                        View All Opportunities
                    </a>
                </p>
                
                <hr style="margin: 25px 0; border: none; border-top: 1px solid #eee;" />
                
                <div style="background: #fef3c7; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b;">
                    <p style="margin: 0; font-size: 14px;"><strong>📊 Unlock your Annual Career Report</strong></p>
                    <p style="margin: 5px 0 0 0; font-size: 13px; color: #666;">See your salary percentile, market trends, and personalized career recommendations.</p>
                    <p style="margin: 8px 0 0 0;">
                        <a href="{settings.APP_URL}/pricing" style="color: #d97706; font-size: 13px; font-weight: 600;">Upgrade to Pro →</a>
                    </p>
                </div>
            </div>
            
            <div style="padding: 15px; text-align: center; color: #9ca3af; font-size: 12px;">
                <p>You're receiving this because you enabled salary alerts on JobScale.</p>
                {self._unsub_footer(user_id)}
            </div>
        </body>
        </html>
        """
        return self.send_email(to, subject, html)

    def send_weekly_career_report(self, to: str, name: str, report: dict, user_id: Optional[int] = None) -> bool:
        """Send weekly career report email (upsell for annual report)"""
        subject = "📊 Your Weekly Career Report"
        
        stats = report.get("career_stats", {})
        salary_info = ""
        if report.get("current_salary", 0) > 0:
            salary_info = f"""
            <div style="background: #eff6ff; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <p style="margin: 0; font-size: 14px;"><strong>Salary Position:</strong> {report.get('percentile', 50)}th percentile</p>
                <p style="margin: 5px 0 0 0; font-size: 13px; color: #666;">Market average for your role: £{report.get('market_average', 0):,}</p>
                <p style="margin: 5px 0 0 0; font-size: 13px; color: #166534; font-weight: 600;">{report.get('better_paying_jobs', 0)} better-paying jobs available</p>
            </div>
            """
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <h2>Your Weekly Career Report 📊</h2>
            
            <p>Hi {name}, here's your career snapshot:</p>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 20px 0;">
                <div style="text-align: center; padding: 15px; background: #f0f9ff; border-radius: 8px;">
                    <div style="font-size: 24px; font-weight: bold; color: #2563eb;">{stats.get('total_applications', 0)}</div>
                    <div style="font-size: 12px; color: #6b7280;">Applications</div>
                </div>
                <div style="text-align: center; padding: 15px; background: #f0fdf4; border-radius: 8px;">
                    <div style="font-size: 24px; font-weight: bold; color: #16a34a;">{stats.get('interviews', 0)}</div>
                    <div style="font-size: 12px; color: #6b7280;">Interviews</div>
                </div>
            </div>
            
            {salary_info}
            
            <p style="margin-top: 25px; text-align: center;">
                <a href="{settings.APP_URL}/analytics"
                   style="background-color: #2563eb; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 8px; display: inline-block;">
                    View Full Report
                </a>
            </p>
            
            <hr style="margin: 25px 0; border: none; border-top: 1px solid #eee;" />
            
            <div style="background: #faf5ff; padding: 15px; border-radius: 8px; text-align: center;">
                <p style="margin: 0; font-weight: 600;">🔓 Unlock Annual Career Report</p>
                <p style="margin: 5px 0; font-size: 13px; color: #666;">Detailed salary analysis, career trajectory, and personalized growth plan.</p>
                <a href="{settings.APP_URL}/pricing" style="color: #7c3aed; font-weight: 600; font-size: 14px;">Upgrade to Pro →</a>
            </div>
            
            {self._unsub_footer(user_id)}
        </body>
        </html>
        """
        return self.send_email(to, subject, html)

    def send_password_reset_email(self, to: str, token: str) -> bool:
        reset_url = f"{settings.APP_URL.rstrip('/')}/reset-password?token={token}"
        subject = "Reset your JobScale password"
        html = f"""
        <html><body style="font-family:Arial,sans-serif;line-height:1.5;color:#0f172a">
          <h2>Password reset</h2>
          <p>We received a request to reset your JobScale password.</p>
          <p><a href="{reset_url}" style="background:#0f172a;color:#fff;padding:12px 18px;border-radius:8px;text-decoration:none;display:inline-block">Reset password</a></p>
          <p style="color:#64748b;font-size:13px">This link expires in 60 minutes. If you did not request this, ignore this email.</p>
        </body></html>
        """
        return self.send_email(to, subject, html)

    def send_verification_email(self, to: str, name: str, token: str) -> bool:
        verify_url = f"{settings.APP_URL.rstrip('/')}/verify-email?token={token}"
        subject = "Verify your JobScale email"
        html = f"""
        <html><body style="font-family:Arial,sans-serif;line-height:1.5;color:#0f172a">
          <h2>Hi {name or 'there'},</h2>
          <p>Confirm your email to secure your JobScale account.</p>
          <p><a href="{verify_url}" style="background:#0d9488;color:#fff;padding:12px 18px;border-radius:8px;text-decoration:none;display:inline-block">Verify email</a></p>
          <p style="color:#64748b;font-size:13px">Link expires in 24 hours.</p>
        </body></html>
        """
        return self.send_email(to, subject, html)


# Singleton
email_service = EmailService()
