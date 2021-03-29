import logging
import os
import sys
import threading
from dataclasses import dataclass
from typing import Generator, Any

import praw
import prawcore

from cardinal.bot import CardinalBot
from cardinal.decorators import command, help

log = logging.getLogger(__name__)


@dataclass
class Submission:
    url: str
    author: str
    id: str
    title: str


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

    def stream_new_submissions(self, subreddit_name: str, skip_existing: bool = True) -> \
            Generator[Submission, Any, None]:
        subreddit = self._reddit.subreddit(subreddit_name)
        for submission in subreddit.stream.submissions(skip_existing=skip_existing):
            url = self._short_base_url + submission.id
            yield Submission(url=url, author=submission.author.name, id=submission.id, title=submission.title)


class SubWatchPlugin(object):
    def __init__(self, cardinal: CardinalBot, config, praw_handler: PrawHandler = PrawHandler()) -> None:
        self._sub_watch_started = False
        self._cardinal = cardinal
        self._channel = ""
        self._thread: threading.Thread
        self._praw_handler = praw_handler

    @staticmethod
    def create(cardinal: CardinalBot, config, praw_handler: PrawHandler) -> 'SubWatchPlugin':
        return SubWatchPlugin(cardinal, config, praw_handler)

    def close(self, cardinal: CardinalBot) -> None:
        pass

    @command(['snbsw'])
    @help("Start sub watch")
    def trigger_init(self, cardinal: CardinalBot, user, channel, msg) -> None:
        if not self._sub_watch_started:
            self._channel = channel
            self._sub_watch_started = True
            self._start_sub_watch()

    def _start_sub_watch(self) -> None:
        self._thread = threading.Thread(target=self._listen_reddit)
        self._thread.start()

    def _listen_reddit(self) -> None:
        while True:
            try:
                for submission in self._praw_handler.stream_new_submissions("linuxmasterrace"):
                    print(f"New post by {submission.author}: {submission.title} - {submission.url}")
                    self._cardinal.sendMsg(
                        channel=self._channel,
                        message=f"New post by {submission.author}: {submission.title} - {submission.url}")
                return
            except prawcore.exceptions.ServerError:
                log.exception("Reddit call failed, restarting...")


entrypoint = SubWatchPlugin
