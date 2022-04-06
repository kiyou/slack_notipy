# slack-notipy
A simple script for sending decorated notifications using Slack Incoming Webhook from Python3.

## Overview
- Use the hostname and the process id as the sender name as default
- Default color scheme for each priority level
- Context Manager for notification:
    - fields which can notify various outputs by passing a dictionary
    - traceback information of an Exception if raised
    - a flag for notifying only when an Exception is raised
    - elapsed time to finish the `with` statement
    - a hash of the `with` statement as a footer as identification
- Decorator for notification
- CLI command

## Requirements
- Python3
- python-dotenv

## Install
Clone this repository and run `pip install .`:

``` bash
git clone https://github.com/kiyou/slack_notipy.git
cd slack_notipy
pip install .
```

or one-liner:

``` bash
pip install git+https://github.com/kiyou/slack_notipy.git
```

To uninstall, use pip:

``` bash
pip uninstall slack_notipy
```

## Usage
1. Get Slack Webhook URL
    https://api.slack.com/messaging/webhooks

1. Set environment variable
    - Add following lines in your profile file (e.g. ~/.bash_profile):

    ``` sh
    export SLACK_WEBHOOK_URL=<YOUR SLACK WEBHOOK_URL (https://hooks.slack.com/services/*****/*****)>
    ```

    - or prepare `.env` in a runtime directory:

    ``` sh
    echo "SLACK_WEBHOOK_URL=<YOUR SLACK WEBHOOK_URL (https://hooks.slack.com/services/*****/*****)>" > .env
    ```

1. Use
    - Context Manager

    ``` python
    from slack_notipy import Notify

    try:
        with Notify("SlackNotify context 1") as f:
            a = sum([i for i in range(1, 101)])
            print(a)
            f.fields=[{"title": "result", "value": str(a)}, ]
        with Notify("SlackNotify context 2"):
            print(1/0)
    except ZeroDivisionError:
        print("Exception called")
    ```

    - Decorator

    ``` python
    from slack_notipy import context_wrapper

    @context_wrapper(name="context_wrapper")
    def calc(a, b):
        c = a/b
        return c
    try:
        d = calc(1, 1)
        d = calc(1, 0)
    except ZeroDivisionError:
        print("Exception called")
    ```

    - CLI on shell environment

    ``` bash
    slack_notipy "test notification"
    ```

## Licence
[MIT](https://opensource.org/licenses/mit-license.php)

## Author
[kiyou](https://github.com/kiyou)
