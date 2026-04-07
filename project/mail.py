"""
Use of "sendgrid" for email sending.

In your local configuration file :

'EMAIL': {
    'service': 'sendgrid',
    'default_sender': {'name': 'your project', 'email': 'youremail@yourdomain.com'},
    'api_url': 'https://api.sendgrid.com/v3/mail/send',
    'api_key': 'SENDGRID_API_KEY'}

for send email example see test_api_sendgrid()
------------------------------------------------------------------------------


Use gmail for send email

In your local configuration file :

'EMAIL': {
    'service': 'gmail',
    'default_sender': {'name': 'your project', 'email': 'youremail@yourdomain.com'},
    'oauth2_file': PATH_TO_OAUTH_JSON_CREDENTIALS_FILE
    }

example: see test_gmail()

FIRST RUN:
a link will be shown in the terminal that you should followed to obtain
a google_refresh_token. Paste this again, and you're set up

See docs at: https://github.com/kootenpv/yagmail

------------------------------------------------------------------------------

"""

import smtplib
import traceback

try:
    from email.MIMEText import MIMEText
except ModuleNotFoundError:
    from email.mime.text import MIMEText

import logging
import os


def test_gmail():
    logging.basicConfig(level=logging.DEBUG)
    pard = {"EMAIL": {"service": "gmail", "oauth2_file": "oauth2_creds.json"}}
    args = {
        "from": {"name": "Gianfranco Messori", "email": "messori.gf@gmail.com"},
        "to": [{"name": "Beppe", "email": "gmessori@gmail.com"}],
        "bcc": [{"name": "GF", "email": "messori.gf@gmail.com"}],
        "subject": "Prova wsgian email",
        "content": "Tutti i nodi vengono al pettine",
    }
    send(pard, args)


def test_api_smtp():
    logging.basicConfig(level=logging.DEBUG)
    pard = {"EMAIL": {"service": "SMTP", "smtp_host": "localhost", "smtp_port": 1025}}
    args = {
        "from": {"name": "Gianfranco Messori", "email": "messori.gf@gmail.com"},
        "to": [{"name": "Beppe", "email": "gmessori@gmail.com"}],
        "subject": "Prova wsgian email",
        "content": "Tutti i nodi vengono al pettine",
    }
    send(pard, args)


def test_api_sendgrid():
    logging.basicConfig(level=logging.DEBUG)
    pard = {
        "EMAIL": {
            "service": "sendgrid",
            "api_url": "https://api.sendgrid.com/v3/mail/send",
            "api_key": os.environ.get("SENDGRID_API_KEY"),
        }
    }
    args = {
        "from": {"name": "Kinder Supreme Team", "email": "messori.gf@gmail.com"},
        "to": [{"name": "Beppe", "email": "gmessori@gmail.com"}],
        "bcc": [{"name": "Gianfranco Messori", "email": "messori.gf@gmail.com"}],
        "subject": "Prova wsgian email",
        "content": "Tutti i nodi vengono al pettine\n O no?",
    }
    send(pard, args)


# ------------------------------------------------------------------- #
def send(pard, args):
    """
    New API Style methods for sending email

    Args:
            to, cc, bcc
            from,
            subject,
            content,
    """
    args.setdefault(
        "to",
        [
            {},
        ],
    )
    args.setdefault("from", {})
    args.setdefault("subject", "")
    args.setdefault("content", "")

    pard.setdefault("EMAIL", {"service": "SMTP"})
    if pard["EMAIL"]["service"] == "SMTP":
        result = smtp_send(pard, args)
    elif pard["EMAIL"]["service"] == "sendgrid":
        result = sendgrid(pard, args)
    elif pard["EMAIL"]["service"] == "gmail":
        result = gmail_send(pard, args)

    else:
        result = {
            "status": "Failure",
            "errors": "EMAIL Service `%(service)s` not available" % pard["EMAIL"],
        }

    mail_log(pard, args, result)
    return result


def smtp_send(pard, args):
    msg = MIMEText(args["content"])
    msg["From"] = "%(name)s <%(email)s>" % args["from"]
    msg["Subject"] = args["subject"]
    msg["To"] = ", ".join(["%(name)s <%(email)s>" % to for to in args["to"]])
    try:
        s = smtplib.SMTP(pard["EMAIL"]["smtp_host"], pard["EMAIL"]["smtp_port"])
        s.sendmail(msg["From"], msg["To"], msg.as_string())
        s.close()
        err = ""
    except:
        err = traceback.format_exc()
    result = {"status": "Success"}
    if err:
        result["status"] = "Failure"
        result["errors"] = err
    return result


def gmail_send(pard, args):
    import yagmail

    yargs = {}
    yargs["to"] = [to["email"] for to in args["to"]]
    if "cc" in args and args["cc"]:
        yargs["cc"] = [cc["email"] for cc in args["cc"]]
    if "bcc" in args and args["bcc"]:
        yargs["bcc"] = [bcc["email"] for bcc in args["bcc"]]
    yargs["subject"] = args["subject"]
    yargs["contents"] = args["content"]
    try:
        yag = yagmail.SMTP(
            args["from"]["email"], oauth2_file=pard["EMAIL"]["oauth2_file"]
        )
        yag.send(**yargs)
        err = ""
    except:
        err = traceback.format_exc()
    result = {"status": "Success"}
    if err:
        result["status"] = "Failure"
        result["errors"] = err
    return result


def sendgrid(pard, args):
    import requests

    from . import json

    api_url = pard["EMAIL"]["api_url"]
    api_key = pard["EMAIL"]["api_key"]

    persz = {"to": args["to"], "subject": args["subject"]}
    if "bcc" in args:
        persz["bcc"] = args["bcc"]
    if "cc" in args:
        persz["cc"] = args["cc"]

    payload = {
        "personalizations": [persz],
        "from": args["from"],
        "content": [{"type": "text/plain", "value": args["content"]}],
    }
    payload = json.encode(payload)
    logging.info(payload)

    headers = {
        "authorization": "Bearer %s" % api_key,
        "content-type": "application/json",
    }

    response = requests.post(api_url, data=payload, headers=headers)

    logging.info(response.status_code)
    return {"status": "Success", "message": response.content}


def mail_log(pard, args, result):
    logging.info("-" * 70)
    logging.info("Sender: %s" % str(args["from"]))
    logging.info("To: %s" % str(args["to"]))
    logging.info("Subject: %s" % args["subject"])
    logging.info("Body:\n%s" % str(args["content"]))
    if result["status"] == "Failure":
        logging.error("Send email failure:")
        logging.error(result["errors"])
