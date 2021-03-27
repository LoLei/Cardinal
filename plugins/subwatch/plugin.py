import threading
import time

from cardinal.bot import CardinalBot
from cardinal.decorators import command, help


class SubWatchPlugin(object):
    def __init__(self, cardinal: CardinalBot, config) -> None:
        self._sub_watch_started = False
        self._cardinal = cardinal
        self._channel = ""
        self._thread: threading.Thread

    def close(self, cardinal: CardinalBot) -> None:
        pass

    @command(['snbsw'])
    @help("Start nuh_bot sub watch")
    @help("Syntax: .snbsw")
    def trigger_init(self, cardinal: CardinalBot, user, channel, msg) -> None:
        if not self._sub_watch_started:
            self._channel = channel
            self._sub_watch_started = True
            self._start_sub_watch()
            self._cardinal.sendMsg(channel=self._channel, message="Started subwatch")

    def _start_sub_watch(self) -> None:
        self._thread = threading.Thread(target=self._listen_reddit)
        self._thread.start()

    def _listen_reddit(self) -> None:
        while True:
            self._cardinal.sendMsg(channel=self._channel, message="foo")
            time.sleep(5)


entrypoint = SubWatchPlugin
