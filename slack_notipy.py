#!/usr/bin/env python
# slack_notipy.py
from nis import cat
import sys
import os
import time
import json
import urllib.request
import urllib.error
import hashlib
from datetime import datetime
import traceback
from dotenv import load_dotenv

format_dict = {
    "success": {
        "title": "Success",
        "color": "#00bb83",
        "priority": "Middle",
    },
    "info": {
        "title": "Info",
        "color": "#009fbb",
        "priority": "Low",
    },
    "warning": {
        "title": "Warning",
        "color": "#ffa32b",
        "priority": "Middle",
    },
    "error": {
        "title": "Error",
        "color": "#ff0a54",
        "priority": "High",
    },
}


def get_slack_webhook_url(env_slack_webhook_url="SLACK_WEBHOOK_URL"):
    """
    get slack_web_hook_url from environmental variable

    parameters
    --------
    env_slack_webhook_url : str, default "SLACK_WEBHOOK_URL"
        name of slack_webhook_url environmental variable

    returns
    ------
    slack_webhook_url : str
        slack_webhook_url load from environmental variable
    """
    slack_webhook_url = os.getenv(env_slack_webhook_url)
    if slack_webhook_url is None:
        raise OSError(f'Environment variable {env_slack_webhook_url} is not set. Please set it or prepare .env file and retry.')
    return slack_webhook_url


def notify(message, message_type="info", name="python", fields=None, title=None, color=None, footer=None):
    """
    Notify a message

    parameters
    --------
    message : str or dict
        a message to send

    message_type : str
        One of "success", "info", "warning", and "error", default "info"

    name : str
        a name of the sender, default "python"

    fields : None or list
        fields to include, default None

    title : str
        title, default None

    color : None or str
        color, default None

    footer : str
        footer, default None

    returns
    ------
    None : None
    """
    try:
        if isinstance(message, str):
            message_json = make_message(text=message, name=name, message_type=message_type, title=title, color=color, footer=footer, fields=fields)
        elif isinstance(message, dict):
            message_json = message
        else:
            raise RuntimeError("Bad type of message is given.")
        json_data = json.dumps(message_json).encode("utf-8")
        request_headers = { 'Content-Type': 'application/json; charset=utf-8' }
        load_dotenv(os.path.join(os.getcwd(), ".env"), verbose=True)
        url = get_slack_webhook_url(env_slack_webhook_url="SLACK_WEBHOOK_URL")
        if url is None:
            raise RuntimeError("SLACK_WEBHOOK_URL is not set.")
        req = urllib.request.Request(url=url, data=json_data, headers=request_headers, method='POST')
        urllib.request.urlopen(req, timeout=5)
    except urllib.error.URLError as url_error:
        raise RuntimeError('Could not reach slack server') from url_error


def make_message(text, message_type="info", name="python", fields=None, title=None, color=None, footer=None):
    """
    Make a message

    parameters
    --------
    message : str or dict
        a message to send

    message_type : str
        One of "success", "info", "warning", and "error", default "info"

    name : str
        a name of the sender, default "python"

    fields : None or list
        fields to include, default None

    title : str
        title, default None

    color : None or str
        color, default None

    footer : str
        footer, default None

    returns
    ------
    dict
    """

    if title is None:
        title = format_dict[message_type]["title"]
    if color is None:
        color = format_dict[message_type]["color"]
    if footer is None:
        footer = f"Slack API called from python on {os.uname()[1]}"
    field_property = {
        "title": "Priority",
        "value": format_dict[message_type]["priority"],
        "short": "true"
    }
    if fields is None:
        fields = [field_property, ]
    else:
        fields.append(field_property)
    default_attachment = {
        "fallback": f"{title} on {os.uname()[1]}: {text}",
        "color": color,
        "author_name": f"{name} on {os.uname()[1]} (PID: {os.getpid()})",
        "title": title,
        "text": text,
        "fields": fields,
        "footer": footer,
        "ts": int(time.time())
    }
    return {"attachments": [default_attachment,]}


class Notify():
    """
    Context manager for notification by Slack Incoming Webhook
    """
    def __init__(self, name="python", timer=True, exception_only=False, send_flag=True, notify_start=False, catch_exception=()):
        self.name = name
        self.hash = hashlib.blake2b(repr(self).encode("utf-8"), digest_size=5).hexdigest()
        self.footer = f"slack_notipy context #{self.hash}"
        self.fields = dict()
        self.timer = timer
        self.exception_only = exception_only
        self.send_flag = send_flag
        self.notify_start = notify_start
        self.start_time = None
        self.end_time = None
        self.catch_exception = catch_exception

    def __enter__(self):
        if self.timer:
            self.start_time = datetime.now()
        if self.exception_only or not self.send_flag or not self.notify_start:
            pass
        else:
            notify(
                "Calculation started.",
                message_type="info",
                name=self.name,
                footer=self.footer
            )
        return self

    def set_fields(self, fields=None):
        """
        Set and convert fields for notification
        """
        if fields is not None:
            self.fields = fields
        if isinstance(self.fields, dict):
            self.fields = [
                {"title": str(key), "value": str(value), "short": "true"}
                for key, value in self.fields.items()
            ]
        else:
            try:
                self.fields = [
                    {"title": "return", "value": str(self.fields), "short": "true"}
                ]
            except:
                self.fields = []

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.set_fields()
        if exc_type is None:
            if self.exception_only or not self.send_flag:
                return True
            if self.timer:
                self.end_time = datetime.now()
                self.fields += [
                    {
                        "title": "Duration",
                        "value": str(self.end_time - self.start_time),
                        "short": "true"
                    },
                ]
            notify(
                "Calculation finished.",
                message_type="success",
                name=self.name,
                footer=self.footer,
                fields=self.fields
            )
            return True
        elif isinstance(exc_value, self.catch_exception):
            if self.exception_only:
                pass
            else:
                notify(
                    "```" + "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)) + "```",
                    message_type="info",
                    title="Exception caught",
                    name=self.name,
                    footer=self.footer,
                    fields=self.fields + [{"title": "Exception type", "value": str(exc_type), "short": "true"}, ]
                )
            return True
        elif isinstance(exc_value, Warning):
            notify(
                "```" + "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)) + "```",
                message_type="warning",
                name=self.name,
                footer=self.footer,
                fields=self.fields + [{"title": "Error type", "value": str(exc_type), "short": "true"}, ]
            )
            return False
        else:
            notify(
                "```" + "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)) + "```",
                message_type="error",
                name=self.name,
                footer=self.footer,
                fields=self.fields + [{"title": "Error type", "value": str(exc_type), "short": "true"}, ]
            )
            return False


def context_wrapper(name="python", timer=True, exception_only=False, catch_exception=()):
    """
    Context wrapper
    """
    def _context_wrapper(func):
        def run(*args, **kwargs):
            with Notify(name=name, timer=timer, exception_only=exception_only, catch_exception=catch_exception) as s:
                result = func(*args, **kwargs)
                s.fields = result
            return result
        return run
    return _context_wrapper


def cli():
    """
    Command line interface of slack_notipy
    """
    notify(sys.argv[1], message_type="info", name="slack_notipy:cli", fields=None, title=None, color=None, footer=None)


if __name__ == "__main__":
    # using context manager
    # notifying result by fields
    with Notify("context 1") as f:
        a = sum([i for i in range(1, 101)])
        f.fields = a

    # notifying Exception and stop
    try:
        with Notify("context 2"):
            print(1 / 0)
    except ZeroDivisionError:
        print("Exception called")

    # notifying Exception and continue by catch_exception
    with Notify("catch exception", catch_exception=(ZeroDivisionError,)) as f:
        print(1 / 0)

    # using decorator to notify return value and duration
    @context_wrapper(name="calc with context wrapper")
    def calc(a, b):
        c = a + b
        return c

    d = calc(1, 1)
