#!/usr/bin/env python
import sys
import os
import time
import json
import urllib.request
import urllib.error

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
    global slack_webhook_url
    slack_webhook_url = os.getenv(env_slack_webhook_url)
    if slack_webhook_url is None:
        import warnings
        warnings.warn('Environmental variable \"{}\" is not set. Please set slack_webhook_url'.format(env_slack_webhook_url))
    return slack_webhook_url


get_slack_webhook_url()


def notify(message, message_type="info", name="python", fields=list(), title=None, color=None, footer=None):
    try:
        if isinstance(message, str):
            message_json = make_message(text=message, name=name, message_type=message_type, title=title, color=color, footer=footer, fields=fields)
        elif isinstance(message, dict):
            message_json = message
        else:
            raise RuntimeError("Bad type of message is given.")
        json_data = json.dumps(message_json).encode("utf-8")
        request_headers = { 'Content-Type': 'application/json; charset=utf-8' }
        req = urllib.request.Request(url=slack_webhook_url, data=json_data, headers=request_headers, method='POST')
        res = urllib.request.urlopen(req, timeout=5)
    except urllib.error.URLError:
        raise Warning('Could not reach slack server')


def make_message(text, name="python", message_type="info", title=None, color=None, footer=None, fields=list()):
    if title is None:
        title = titles[message_type]
    if color is None:
        color = colors[message_type]
    if footer is None:
        footer = "Slack API called from python on {}".format(os.uname()[1])
    field_property = {
        "title": "Priority",
        "value": priorities[message_type],
        "short": "true"
    }
    default_attachment = {
        "fallback": "{} on {}: {}".format(title, os.uname()[1], text),
        "color": color,
        "author_name": "{} on {} (PID: {})".format(name, os.uname()[1], os.getpid()),
        "title": title,
        "text": text,
        "fields": fields + [field_property,],
        "footer": footer,
        "ts": int(time.time())
    }
    return {"attachments": [default_attachment,]}


class Notify():
    def __init__(self, name="python", timer=True, error_only=False, send_flag=True):
        import hashlib
        self.name = name
        self.hash = hashlib.blake2b(repr(self).encode("utf-8"), digest_size=5).hexdigest()
        self.footer = "slack_notipy context #{}".format(self.hash)
        self.fields = dict()
        self.timer = timer
        self.error_only = error_only
        self.send_flag = send_flag

    def __enter__(self):
        if self.timer:
            from datetime import datetime
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

    def __exit__(self, e_type, value, tb):
        if isinstance(self.fields, dict):
            self.fields = [{"title": str(key), "value": str(value), "short": "true"} for key, value in self.fields.items()]
        if e_type is None:
            if self.error_only or not self.send_flag:
                return True
            if self.timer:
                from datetime import datetime
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
        elif isinstance(value, Warning):
            import traceback
            notify(
                "```" + "".join(traceback.format_exception(etype=e_type, value=value, tb=tb)) + "```",
                message_type="warning",
                name=self.name,
                footer=self.footer,
                fields=self.fields + [{"title": "Error type", "value": str(e_type), "short": "true"}, ]
            )
            return False
        else:
            import traceback
            notify(
                "```" + "".join(traceback.format_exception(etype=e_type, value=value, tb=tb)) + "```",
                message_type="error",
                name=self.name,
                footer=self.footer,
                fields=self.fields + [{"title": "Error type", "value": str(e_type), "short": "true"}, ]
            )
            return False


def context_wrapper(name="python", timer=True, error_only=False):
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
    notify(sys.argv[0], message_type="info", name="python", fields=list(), title=None, color=None, footer=None)


if __name__ == "__main__":
    @context_wrapper(name="calc with context wrapper")
    def calc(a, b):
        c = a/b
        return c
    try:
        d = calc(1, 1)
        d = calc(1, 0)
    except Exception:
        print("Exception called")

    try:
        with Notify("calc_context 1") as f:
            a = sum([i for i in range(1, 101)])
            print(a)
            f.fields = {"result": a}
        with Notify("calc context 2"):
            print(1/0)
    except Exception:
        print("Exception called")
