#!/usr/bin/env python
# slack_notipy.py
import os
import json
from socket import gethostname
from urllib.request import Request, urlopen
from urllib.error import URLError
from hashlib import blake2b
from datetime import datetime
from traceback import format_exception


with open(os.path.join(os.path.dirname(__file__), "config.json"), mode="r", encoding="utf-8") as f:
    config_dict = json.load(f)
    format_dict = config_dict["format"]
    context_message_dict = config_dict["context_message"]


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


def notify(message, message_type="info", name="python", fields=None, title=None, color=None, footer=None, include_priority=False):
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

    include_priority : bool
        priority, default False

    returns
    ------
    None : None
    """
    try:
        if isinstance(message, str):
            message_json = make_message(text=message, name=name, message_type=message_type, title=title, color=color, footer=footer, fields=fields, include_priority=include_priority)
        elif isinstance(message, dict):
            message_json = message
        else:
            raise RuntimeError("Bad type of message is given.")
        json_data = json.dumps(message_json).encode("utf-8")
        request_headers = { 'Content-Type': 'application/json; charset=utf-8' }
        try:
            from dotenv import load_dotenv
            load_dotenv(os.path.join(os.getcwd(), ".env"), verbose=True)
        except ModuleNotFoundError:
            pass
        url = get_slack_webhook_url(env_slack_webhook_url="SLACK_WEBHOOK_URL")
        if url is None:
            raise RuntimeError("SLACK_WEBHOOK_URL is not set.")
        req = Request(url=url, data=json_data, headers=request_headers, method='POST')
        urlopen(req, timeout=config_dict["timeout"])
    except URLError as url_error:
        raise RuntimeError('Could not reach slack server') from url_error


def make_message(text, message_type="info", name="python", fields=None, title=None, color=None, footer=None, include_priority=False):
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

    include_priority : bool
        priority, default False

    returns
    ------
    dict
    """
    if title is None:
        title = format_dict[message_type]["title"]
    if color is None:
        color = format_dict[message_type]["color"]
    if footer is None:
        footer = f"Slack API called from python on {gethostname()}"
    if fields is None:
        fields = []
    if include_priority:
        field_property = {
            "title": "Priority",
            "value": format_dict[message_type]["priority"],
            "short": "true"
        }
        fields.append(field_property)
    default_attachment = {
        "fallback": f"{title} on {gethostname()}: {text}",
        "color": color,
        "author_name": f"{name} on {gethostname()} (PID: {os.getpid()})",
        "title": title,
        "text": text,
        "fields": fields,
        "footer": footer,
        "ts": int(datetime.now().timestamp())
    }
    return {"attachments": [default_attachment,]}


class Notify():
    """
    Context manager for notification by Slack Incoming Webhook
    """
    def __init__(self, name="python", timer=True, exception_only=False, send_flag=True, notify_start=False, catch_exception=()):
        self.name = name
        self.hash = blake2b(repr(self).encode("utf-8"), digest_size=5).hexdigest()
        self.footer = f"slack_notipy context manager #{self.hash}"
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
                context_message_dict["enter"],
                message_type="info",
                name=self.name,
                footer=self.footer
            )
        return self

    def _convert_fields(self):
        """
        convert fields for notification
        """
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
            except ValueError:
                self.fields = []

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._convert_fields()
        if self.timer:
            self.end_time = datetime.now()
            self.fields += [
                {
                    "title": "Duration",
                    "value": str(self.end_time - self.start_time),
                    "short": "true"
                },
            ]
        if exc_type is None:
            if self.exception_only or not self.send_flag:
                return True
            notify(
                context_message_dict["exit"],
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
                    "```" + "".join(format_exception(exc_type, exc_value, exc_traceback)) + "```",
                    message_type="info",
                    title="Exception caught",
                    name=self.name,
                    footer=self.footer,
                    fields=self.fields + [{"title": "Exception type", "value": str(exc_type), "short": "true"}, ]
                )
            return True
        elif isinstance(exc_value, Warning):
            notify(
                "```" + "".join(format_exception(exc_type, exc_value, exc_traceback)) + "```",
                message_type="warning",
                name=self.name,
                footer=self.footer,
                fields=self.fields + [{"title": "Error type", "value": str(exc_type), "short": "true"}, ]
            )
            return False
        else:
            notify(
                "```" + "".join(format_exception(exc_type, exc_value, exc_traceback)) + "```",
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
                s.footer = f"slack_notipy decorator #{s.hash}"
                result = func(*args, **kwargs)
                s.fields = result
            return result
        return run
    return _context_wrapper


def cli():
    """
    Command line interface of slack_notipy
    """
    import argparse
    ap = argparse.ArgumentParser(description="Sending decorated notifications using Slack Incoming Webhook from Python3")
    ap.add_argument("message", type=str, help="message to send")
    ap.add_argument("--name", type=str, default="slack_notipy:cli", help="name of sender, default: slack_notipy:cli")
    ap.add_argument("--title", type=str, default=None, help="title, default: default name corresponding to message type")
    ap.add_argument("--message_type", type=str, default="info", help="message type, default: info")
    ap.add_argument("--color", type=str, default=None, help="color, default: default color scheme corresponding to message type")
    ap.add_argument("--footer", type=str, default=f"slack_notipy:cli on {gethostname()}", help="footer, default: slack_notipy:cli on [HOSTNAME]")
    args = ap.parse_args()
    notify(
        args.message,
        message_type=args.message_type,
        name=args.name,
        fields=None,
        title=args.title,
        color=args.color,
        footer=args.footer,
        include_priority=False,
    )


if __name__ == "__main__":
    # using context manager
    # notifying a value by fields
    with Notify("context 1") as f:
        a = sum([i for i in range(1, 101)])
        f.fields = a

    # notifying multiple values by specifying dictionary to fields
    with Notify("context 2") as f:
        formula = "1 + 1"
        f.fields = {"formula": formula, "results": eval(formula)}

    # notifying Exception and stop
    try:
        with Notify("exception in context"):
            print(1 / 0)
    except ZeroDivisionError:
        print("Exception called")

    # notifying Exception and continue by catch_exception
    with Notify("catch exception", catch_exception=(ZeroDivisionError,)) as f:
        print(1 / 0)

    # using decorator to notify return value and duration
    @context_wrapper(name="calc with context wrapper")
    def calc(a, b):
        """
        example calculation
        """
        return a / b

    c = calc(1, 1)

    try:
        d = calc(1, 0)
    except ZeroDivisionError:
        print("Exception called")
