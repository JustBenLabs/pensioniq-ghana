import os
import smtplib

from email.message import EmailMessage


def send_password_reset_email(
    recipient_email: str,
    reset_url: str,
) -> None:

    smtp_host = os.getenv(
        "PENSIONIQ_SMTP_HOST"
    )

    smtp_port = int(
        os.getenv(
            "PENSIONIQ_SMTP_PORT",
            "587",
        )
    )

    smtp_username = os.getenv(
        "PENSIONIQ_SMTP_USERNAME"
    )

    smtp_password = os.getenv(
        "PENSIONIQ_SMTP_PASSWORD"
    )

    from_email = os.getenv(
        "PENSIONIQ_FROM_EMAIL"
    )

    from_name = os.getenv(
        "PENSIONIQ_FROM_NAME",
        "PensionIQ Ghana",
    )


    if not all(
        [
            smtp_host,
            smtp_username,
            smtp_password,
            from_email,
        ]
    ):

        raise RuntimeError(
            "SMTP email configuration is incomplete."
        )


    message = EmailMessage()

    message["Subject"] = (
        "Reset your PensionIQ password"
    )

    message["From"] = (
        f"{from_name} <{from_email}>"
    )

    message["To"] = recipient_email


    message.set_content(
        f"""
Hello,

We received a request to reset the password for your PensionIQ Ghana account.

Use the link below to choose a new password:

{reset_url}

This link expires in 15 minutes and can only be used once.

If you did not request a password reset, you can ignore this email.

PensionIQ Ghana
Retirement Intelligence Platform
"""
    )


    message.add_alternative(
        f"""
<!DOCTYPE html>

<html>

<body
    style="
        font-family: Arial, sans-serif;
        background: #f4f7f6;
        padding: 30px;
        color: #17211e;
    "
>

    <div
        style="
            max-width: 560px;
            margin: auto;
            background: white;
            padding: 32px;
            border-radius: 14px;
        "
    >

        <h2
            style="
                color: #123d33;
                margin-top: 0;
            "
        >
            Reset your PensionIQ password
        </h2>

        <p>
            We received a request to reset the
            password for your PensionIQ Ghana account.
        </p>

        <p>
            Click the button below to choose
            a new password.
        </p>

        <p style="margin: 28px 0;">

            <a
                href="{reset_url}"
                style="
                    display: inline-block;
                    padding: 13px 22px;
                    background: #123d33;
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: bold;
                "
            >
                Reset Password
            </a>

        </p>

        <p
            style="
                font-size: 13px;
                color: #68756f;
            "
        >
            This link expires in 15 minutes
            and can only be used once.
        </p>

        <p
            style="
                font-size: 13px;
                color: #68756f;
            "
        >
            If you did not request a password reset,
            simply ignore this email.
        </p>

        <hr
            style="
                border: 0;
                border-top: 1px solid #dce5e1;
                margin: 28px 0;
            "
        >

        <strong>
            PensionIQ Ghana
        </strong>

        <p
            style="
                margin-top: 3px;
                font-size: 11px;
                color: #68756f;
            "
        >
            Retirement Intelligence Platform
        </p>

    </div>

</body>

</html>
""",
        subtype="html",
    )


    with smtplib.SMTP(
        smtp_host,
        smtp_port,
        timeout=20,
    ) as smtp:

        smtp.ehlo()

        smtp.starttls()

        smtp.ehlo()

        smtp.login(
            smtp_username,
            smtp_password,
        )

        smtp.send_message(
            message
        )