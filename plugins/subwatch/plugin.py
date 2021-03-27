import os
import sys
import threading
from typing import Generator, Any

import praw

from cardinal.bot import CardinalBot
from cardinal.decorators import command, help


class SubWatchPlugin(object):
    def __init__(self, cardinal: CardinalBot, config) -> None:
        self._sub_watch_started = False
        self._cardinal = cardinal
        self._channel = ""
        self._thread: threading.Thread
        self._praw_handler = PrawHandler()

    def close(self, cardinal: CardinalBot) -> None:
        pass

    @command(['snbsw'])
    @help("Start nuh_bot sub watch")
    def trigger_init(self, cardinal: CardinalBot, user, channel, msg) -> None:
        if not self._sub_watch_started:
            self._channel = channel
            self._sub_watch_started = True
            self._start_sub_watch()

    def _start_sub_watch(self) -> None:
        self._thread = threading.Thread(target=self._listen_reddit)
        self._thread.start()

    def _listen_reddit(self) -> None:
        for url in self._praw_handler.stream_new_submissions("linuxmasterrace"):
            self._cardinal.sendMsg(channel=self._channel, message=url)


class PrawHandler:
    def __init__(self) -> None:
        self._client_id = os.environ.get("REDDIT_API_CLIENT_ID")
        self._client_secret = os.environ.get("REDDIT_API_CLIENT_SECRET")
        self._client_user = os.environ.get("REDDIT_API_CLIENT_USER")
        self._version = "0.0.1"
        self._reddit = praw.Reddit(
            client_id=self._client_id,
            client_secret=self._client_secret,
            user_agent=f"{sys.platform}:{self._client_id}:{self._version} (by u/{self._client_user})"
        )
        self._short_base_url = "https://redd.it/"

    def stream_new_submissions(self, subreddit_name: str) -> Generator[str, Any, None]:
        subreddit = self._reddit.subreddit(subreddit_name)
        for submission in subreddit.stream.submissions(skip_existing=True):
            url = self._short_base_url + str(submission)
            yield url


entrypoint = SubWatchPlugin
