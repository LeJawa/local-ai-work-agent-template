from typing import cast
import os
from pygments.console import esc
import imaplib
import email
from email.header import decode_header
from getpass import getpass
from bs4 import BeautifulSoup
from email import message_from_bytes
from email.policy import default
from markdownify import markdownify
import html2text

IMAP_HOST = os.getenv("EMAIL_IMAP_SERVER") or "imap.mailbox.org"
USERNAME = os.getenv("EMAIL_ADDRESS") or "luis.escobar@mailbox.org"
PASSWORD = os.getenv("EMAIL_PASSWORD") or getpass("Password: ")


def extract_email_body(raw_email: bytes, extractor_fn) -> str:
    msg = message_from_bytes(raw_email, policy=default)

    # Prefer plain text
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            return part.get_content().strip()

    # Fall back to HTML
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            html = part.get_content()
            return extractor_fn(html)

    return ""

def html_to_markdown(html: str) -> str:
    converter = html2text.HTML2Text()
    converter.body_width = 0  # don't wrap lines
    converter.ignore_images = True
    converter.ignore_emphasis = False
    converter.ignore_links = False

    return converter.handle(html)


def html_to_text_bs4(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Remove noisy tags
    for tag in soup(["script", "style", "head", "meta", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # Normalize whitespace
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]

    return "\n".join(lines)

def html_to_text(html: str) -> str:
    converter = html2text.HTML2Text()
    converter.ignore_links = True
    converter.ignore_images = True
    converter.body_width = 0
    return converter.handle(html).strip()

def recursive_print_message(msg):
    content_type = msg.get_content_type()

    if not msg.is_multipart() or content_type == "text/plain":
        body = msg.get_payload(decode=True)
        charset = msg.get_content_charset() or "utf-8"
        print(body.decode(charset, errors="replace"))
    else:
        for part in msg.walk():
            if part == msg:
                continue
            disposition = part.get_content_disposition()
            if disposition == "attachment":
                continue
            recursive_print_message(part)

with imaplib.IMAP4_SSL(IMAP_HOST) as imap:
    imap.login(USERNAME, PASSWORD)

    imap.select("Cocina")  # mailbox name

    status, data = imap.search(None, "ALL")
    if status != "OK":
        raise RuntimeError("Search failed")

    message_ids = data[0].split()

    for msg_id in message_ids[-10:]:  # latest 10
        status, msg_data = imap.fetch(msg_id, "(RFC822)")
        if status != "OK" or msg_data[0] is None:
            continue

        raw_email: bytes = cast(bytes, msg_data[0][1])
        msg = email.message_from_bytes(raw_email)

        subject, encoding = decode_header(msg.get("Subject", ""))[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8", errors="replace")

        sender = msg.get("From")
        date = msg.get("Date")

        print("From:", sender)
        print("Date:", date)
        print("Subject:", subject)

        with open("bs4.html", "a", encoding="utf-8") as f:
            f.write(f"From: {sender}\n")
            f.write(f"Date: {date}\n")
            f.write(f"Subject: {subject}\n")
            f.write(extract_email_body(raw_email, html_to_text_bs4))
            f.write("\n---------------------------------------------------------------------------\n")
        with open("plain.html", "a", encoding="utf-8") as f:
            f.write(f"From: {sender}\n")
            f.write(f"Date: {date}\n")
            f.write(f"Subject: {subject}\n")
            f.write(extract_email_body(raw_email, html_to_text))
            f.write("\n---------------------------------------------------------------------------\n")
        with open("markdownify.md", "a", encoding="utf-8") as f:
            f.write(f"From: {sender}\n")
            f.write(f"Date: {date}\n")
            f.write(f"Subject: {subject}\n")
            f.write(extract_email_body(raw_email, html_to_markdown))
            f.write("\n---------------------------------------------------------------------------\n")

        # if msg.is_multipart():
        #     print("Is multipart:", True)
        #     print("Content type:", msg.get_content_type())

        #     for part in msg.walk():
        #         content_type = part.get_content_type()
        #         disposition = part.get_content_disposition()

        #         if content_type == "text/plain" and disposition != "attachment":
        #             body = part.get_payload(decode=True)
        #             charset = part.get_content_charset() or "utf-8"
        #             print(body.decode(charset, errors="replace"))
        #             break
        # else:
        #     print("Is multipart:", False)
        #     body = msg.get_payload(decode=True)
        #     charset = msg.get_content_charset() or "utf-8"
        #     print(body.decode(charset, errors="replace"))

        print("-" * 80)

    imap.logout()
