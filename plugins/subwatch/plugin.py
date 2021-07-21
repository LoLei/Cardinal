import logging
import os
import sys
import threading
import time
from dataclasses import dataclass
from typing import Generator, Any

import praw
import prawcore

from cardinal.bot import CardinalBot
from cardinal.decorators import command, help, event

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
            max_age_seconds = 60 * 60
            if int(time.time()) - int(submission.created_utc) > max_age_seconds:
                log.warning(f"Got submission {submission.id} created at {submission.created_utc}")
                log.warning(f"Ignoring due to it being older than max age seconds ({max_age_seconds})")
                continue
            url = self._short_base_url + submission.id
            yield Submission(url=url, author=submission.author.name, id=submission.id, title=submission.title)


class SubWatchPlugin(object):
    def __init__(self, cardinal: CardinalBot, config, praw_handler: PrawHandler = PrawHandler()) -> None:
        self._sub_watch_started = False
        self._cardinal = cardinal
        self._updated_cardinal: CardinalBot = cardinal
        default_channel = "##bot-testing"
        self._channel = os.environ.get("CHANNEL", default_channel)
        if self._channel == default_channel:
            log.warning(f"Using default channel: {default_channel}")
        self._thread: threading.Thread
        self._praw_handler = praw_handler

    @staticmethod
    def create(cardinal: CardinalBot, config, praw_handler: PrawHandler) -> 'SubWatchPlugin':
        return SubWatchPlugin(cardinal, config, praw_handler)

    def close(self, cardinal: CardinalBot) -> None:
        pass

    @command(['dbgnb'])
    def debug_msg_nb(self, cardinal: CardinalBot, user, channel: str, msg) -> None:
        """ Method used for debugging purposes """
        nick, ident, vhost = user
        # Send with passed-in object
        cardinal.sendMsg(channel, f"({nick}) debug 1 {time.time()}")
        # Send with original member variable object
        self._cardinal.sendMsg(self._channel, f"({nick}) debug 2 {time.time()}")
        # Send with updated original member variable object
        self._updated_cardinal.sendMsg(self._channel, f"({nick}) debug 3 {time.time()}")

    @event('irc.privmsg')
    def event_privmsg(self, cardinal: CardinalBot, user, channel: str, msg: str) -> None:
        if msg == "snbsw":
            log.debug("EVENT: event_privmsg got command snbsw")
            self.trigger_init(cardinal, user, self._channel, msg)

    @event('irc.notice')
    def event_notice(self, cardinal: CardinalBot, user, channel: str, msg: str) -> None:
        self.trigger_init(cardinal, user, self._channel, msg)

    @command(['snbsw'])
    @help("Start sub watch")
    def trigger_init(self, cardinal: CardinalBot, user, channel, msg) -> None:
        if not self._sub_watch_started:
            self._sub_watch_started = True
            self._updated_cardinal = cardinal
            self._start_sub_watch()

    def _start_sub_watch(self) -> None:
        default_sub = "test"
        subreddit = os.environ.get("SUBREDDIT", default_sub)
        if subreddit == default_sub:
            log.warning(f"Using default sub: r/{default_sub}")
        self._thread = threading.Thread(target=self._listen_reddit, args=(subreddit,))
        self._thread.start()

    def _listen_reddit(self, subreddit: str) -> None:
        while True:
            try:
                for submission in self._praw_handler.stream_new_submissions(subreddit):
                    print(f"New post by {submission.author}: {submission.title} - {submission.url}")
                    self._cardinal.sendMsg(
                        channel=self._channel,
                        message=f"New post by {submission.author}: {submission.title} - {submission.url}")
                return
            except (prawcore.exceptions.ServerError, prawcore.exceptions.RequestException,
                    prawcore.exceptions.ResponseException):
                log.exception("Reddit API call failed, restarting...")
                self._praw_handler = PrawHandler()
                self._cardinal = self._updated_cardinal


entrypoint = SubWatchPlugin
