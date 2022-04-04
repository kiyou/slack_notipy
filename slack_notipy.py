#!/usr/bin/env python
# slack_notipy.py
import sys
import os
import time
import json
import urllib.request
import urllib.error
import hashlib
from datetime import datetime
import warnings
import traceback

colors = {
    "success": "#00bb83",
    "info": "#009fbb",
    "warning": "#ffa32b",
    "error": "#ff0a54",
}

titles = {
    "success": "Success",
    "info": "Info",
    "warning": "Warning",
    "error": "Error",
}

priorities = {
    "success": "Middle",
    "info": "Low",
    "warning": "Middle",
    "error": "High",
}

def get_slack_webhook_url(env_slack_webhook_url="SLACK_WEBHOOK_URL"):
    """
    get slack_web_hook_url from environmental variable

    parameters
    --------
    env_slack_webhook_url : str
        name of slack_webhook_url environmental variable

    returns
    ------
    slack_webhook_url : str
        slack_webhook_url load from environmental variable
    """
    slack_webhook_url = os.getenv(env_slack_webhook_url)
    if slack_webhook_url is None:
        warnings.warn(f'Environmental variable {env_slack_webhook_url} is not set. Please set slack_webhook_url')
    return slack_webhook_url

SLACK_WEBHOOK_URL = get_slack_webhook_url(env_slack_webhook_url="SLACK_WEBHOOK_URL")


def notify(message, message_type="info", name="python", fields=None, title=None, color=None, footer=None):
    """
    Notify a message

    parameters
    --------
    message : str or dict
        a message to send

    message_type : str
        One of "success", "info", "warning", and "error"

    name : str
        a name of the sender

    fields : None or list
        fields to include

    title : str
        title

    color : None or str
        color

    footer : str
        footer

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
        req = urllib.request.Request(url=SLACK_WEBHOOK_URL, data=json_data, headers=request_headers, method='POST')
        urllib.request.urlopen(req, timeout=5)
    except urllib.error.URLError as url_error:
        raise Warning('Could not reach slack server') from url_error


def make_message(text, name="python", message_type="info", title=None, color=None, footer=None, fields=None):
    """
    Make a message

    parameters
    --------
    text : str
        a text message to send

    name : str
        a name of the sender

    message_type : str
        "info"

    title : str
        title

    color : None or str
        color

    footer : str
        footer

    fields : None or list
        fields to include

    returns
    ------
    dictionary
    """

    if title is None:
        title = titles[message_type]
    if color is None:
        color = colors[message_type]
    if footer is None:
        footer = f"Slack API called from python on {os.uname()[1]}"
    field_property = {
        "title": "Priority",
        "value": priorities[message_type],
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
    Context manager
    """
    def __init__(self, name="python", timer=True, error_only=False, send_flag=True):
        self.name = name
        self.hash = hashlib.blake2b(repr(self).encode("utf-8"), digest_size=5).hexdigest()
        self.footer = f"slack_notipy context #{self.hash}"
        self.fields = dict()
        self.timer = timer
        self.error_only = error_only
        self.send_flag = send_flag
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        if self.timer:
            self.start_time = datetime.now()
        if self.error_only or not self.send_flag:
            return self
        notify(
            "Calculation started.",
            message_type="info",
            name=self.name,
            footer=self.footer
        )
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if isinstance(self.fields, dict):
            self.fields = [{"title": str(key), "value": str(value), "short": "true"} for key, value in self.fields.items()]
        if exc_type is None:
            if self.error_only or not self.send_flag:
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


def context_wrapper(name="python", timer=True, error_only=False):
    """
    Context wrapper
    """
    def _context_wrapper(func):
        def run(*args, **kwargs):
            with Notify(name=name, timer=timer, error_only=error_only) as s:
                result = func(*args, **kwargs)
                if isinstance(result, (dict, list)):
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
    @context_wrapper(name="calc with context wrapper")
    def calc(a, b):
        c = a/b
        return c
    try:
        d = calc(1, 1)
        d = calc(1, 0)
    except ZeroDivisionError:
        print("Exception called")

    try:
        with Notify("calc_context 1") as f:
            a = sum([i for i in range(1, 101)])
            print(a)
            f.fields = {"result": a}
        with Notify("calc context 2"):
            print(1/0)
    except ZeroDivisionError:
        print("Exception called")
