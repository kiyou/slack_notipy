from setuptools import setup

setup(
    name='slack_notipy',
    version="0.1.0",
    description="A simple script for sending decorated notifications using Slack Incoming Webhook from Python3.",
    long_description="A simple script for sending decorated notifications using Slack Incoming Webhook from Python3.",
    url='https://github.com/kiyou/slack_notipy',
    author='kiyou',
    author_email='',
    license='MIT',
    classifiers=[
        # https://pypi.python.org/pypi?:action=list_classifiers
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
    ],
    keywords='tools',
    install_requires=["python-dotenv",],
    py_modules=["slack_notipy"],
    entry_points={
        'console_scripts':[
            'slack_notipy = slack_notipy:cli',
        ],
    },
)