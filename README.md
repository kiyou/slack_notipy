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
    # load
    from slack_notipy import Notify

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

    ```

    - Decorator

    ``` python
    from slack_notipy import context_wrapper

    # using decorator to notify return value and duration
    @context_wrapper(name="calc with context wrapper")
    def calc(a, b):
        """
        example calculation
        """
        return a + b

    c = calc(1, 1)

    try:
        d = calc(1, 0)
    except ZeroDivisionError:
        print("Exception called")
    ```

    - CLI on shell environment

    ``` bash
    slack_notipy -h
    # usage: slack_notipy [-h] [--name NAME] [--title TITLE] [--message_type MESSAGE_TYPE] [--color COLOR] [--footer FOOTER] message
    # 
    # Sending decorated notifications using Slack Incoming Webhook from Python3
    # 
    # positional arguments:
    #   message               message to send
    # 
    # options:
    #   -h, --help            show this help message and exit
    #   --name NAME           name of sender, default: slack_notipy:cli
    #   --title TITLE         title, default: default name corresponding to message type
    #   --message_type MESSAGE_TYPE
    #                         message type, default: info
    #   --color COLOR         color, default: default color scheme corresponding to message type
    #   --footer FOOTER       footer, default: slack_notipy:cli on [HOSTNAME]Sending decorated notifications using Slack Incoming Webhook from Python3
    slack_notipy "test notification"
    ```

## Licence
[MIT](https://opensource.org/licenses/mit-license.php)

## Author
[kiyou](https://github.com/kiyou)
