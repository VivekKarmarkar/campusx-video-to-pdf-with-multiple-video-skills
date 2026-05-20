"""Send an email with a PDF attachment via the gws CLI.

Mirrors the /email skill's transport (gws gmail users messages send, sender
vivekkmk.assistant@gmail.com) but adds attachment support — the upstream
encode_email.py doesn't carry attachments.
"""

from __future__ import annotations

import argparse
import mimetypes
import subprocess
import sys
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path

SENDER = "vivekkmk.assistant@gmail.com"


def build_eml(to: str, subject: str, body: str, attachments: list[Path]) -> bytes:
    msg = MIMEMultipart()
    msg["From"] = SENDER
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    for path in attachments:
        ctype, encoding = mimetypes.guess_type(str(path))
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        part = MIMEBase(maintype, subtype)
        part.set_payload(path.read_bytes())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=path.name)
        msg.attach(part)

    return msg.as_bytes()


def send(to: str, subject: str, body: str, attachments: list[Path]) -> None:
    # Gmail's users.messages.send supports RFC-822 messages via multipart upload.
    # Inline --json hits ARG_MAX on >~1MB attachments, so stream from disk instead.
    raw = build_eml(to, subject, body, attachments)
    eml_path = Path("_outbox.eml")  # gws requires upload paths within CWD
    eml_path.write_bytes(raw)

    result = subprocess.run(
        [
            "gws",
            "gmail",
            "users",
            "messages",
            "send",
            "--params",
            '{"userId": "me"}',
            "--upload",
            str(eml_path),
            "--upload-content-type",
            "message/rfc822",
        ],
        capture_output=True,
        text=True,
    )
    eml_path.unlink(missing_ok=True)

    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        sys.exit(f"gws send failed (code {result.returncode})")
    print(result.stdout)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--to", required=True)
    p.add_argument("--subject", required=True)
    p.add_argument("--body", required=True)
    p.add_argument("--attach", action="append", default=[])
    args = p.parse_args()
    paths = [Path(a) for a in args.attach]
    for ap in paths:
        if not ap.is_file():
            sys.exit(f"attachment not found: {ap}")
    send(args.to, args.subject, args.body, paths)
