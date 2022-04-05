# slack-notipy
A simple script for sending decorated notifications using Slack Incoming Webhook from Python3.

## Overview
- Supports hundling exceptions and fields in attachments for slack incoming webhook.
- Use the hostname and the process id as the sender name
- Automatically generates a footer with a hash for Context Manager
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
1. Set environment variable
    - Add following lines in your profile file (e.g. ~/.bash_profile):

    ``` sh
    export SLACK_WEBHOOK_URL=<YOUR SLACK WEBHOOK_URL (https://hooks.slack.com/services/*****/*****)>
    ```

    - or prepare `.env` in a runtime directory:

    ``` sh
    echo "SLACK_WEBHOOK_URL=<YOUR SLACK WEBHOOK_URL (https://hooks.slack.com/services/*****/*****)>" > .env
    ```

2. Use
    - CLI
    ``` bash
    slack_notipy "test notification"
    ```

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

## Licence
[MIT](https://opensource.org/licenses/mit-license.php)

## Author
[kiyou](https://github.com/kiyou)
