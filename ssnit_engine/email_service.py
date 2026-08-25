import html
import json
import os
import urllib.error
import urllib.request


def send_password_reset_email(
    recipient_email: str,
    reset_url: str,
) -> None:
    """
    Send a PensionIQ Ghana password-reset email
    using the Resend HTTPS API.
    """

    api_key = os.getenv("RESEND_API_KEY")

    if not api_key:
        raise RuntimeError(
            "RESEND_API_KEY is not configured."
        )

    from_email = os.getenv(
        "PENSIONIQ_FROM_EMAIL",
        "PensionIQ Ghana <onboarding@resend.dev>",
    )

    safe_reset_url = html.escape(
        reset_url,
        quote=True,
    )

    payload = {
        "from": from_email,
        "to": [recipient_email],
        "subject": "Reset your PensionIQ Ghana password",
        "html": f"""
        <div style="
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            line-height: 1.6;
        ">
            <h2>PensionIQ Ghana</h2>

            <p>
                We received a request to reset the password
                for your PensionIQ Ghana account.
            </p>

            <p>
                Click the button below to create a new password.
            </p>

            <p style="margin: 30px 0;">
                <a
                    href="{safe_reset_url}"
                    style="
                        background-color: #111827;
                        color: white;
                        padding: 12px 20px;
                        text-decoration: none;
                        border-radius: 6px;
                        display: inline-block;
                    "
                >
                    Reset Password
                </a>
            </p>

            <p>
                This password-reset link expires in 15 minutes.
            </p>

            <p>
                If you did not request this password reset,
                you can ignore this email.
            </p>

            <hr>

            <p style="font-size: 12px;">
                PensionIQ Ghana provides pension estimates
                and analytical tools. It is not an official
                SSNIT platform.
            </p>
        </div>
        """,
        "text": (
            "PensionIQ Ghana\n\n"
            "We received a request to reset your password.\n\n"
            f"Reset your password here:\n{reset_url}\n\n"
            "This link expires in 15 minutes.\n\n"
            "If you did not request this password reset, "
            "you can ignore this email."
        ),
    }

    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "PensionIQ-Ghana/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=30,
        ) as response:
            if response.status not in (200, 201):
                raise RuntimeError(
                    f"Resend returned status {response.status}."
                )

    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"Resend API error {exc.code}: {error_body}"
        ) from exc

    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Unable to connect to Resend: {exc.reason}"
        ) from exc