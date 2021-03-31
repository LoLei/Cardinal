from unittest.mock import MagicMock, call

from cardinal.bot import CardinalBot
from plugins.subwatch.plugin import PrawHandler, SubWatchPlugin, Submission


def test_subwatch():
    cardinal = CardinalBot()
    cardinal.sendMsg = MagicMock()

    praw_handler = PrawHandler()
    praw_handler.stream_new_submissions = MagicMock()
    submissions = [Submission("url1", "author1", "id1", "title1"),
                   Submission("url2", "author2", "id2", "title2")]
    praw_handler.stream_new_submissions.return_value = (Submission(url=s.url, author=s.author, id=s.id, title=s.title)
                                                        for s in submissions)

    subwatch = SubWatchPlugin.create(cardinal, {}, praw_handler)
    subwatch.trigger_init(cardinal, "", "##bot-testing", "")

    calls = [call(channel="##bot-testing", message="New post by author1: title1 - url1"),
             call(channel="##bot-testing", message="New post by author2: title2 - url2")]
    cardinal.sendMsg.assert_has_calls(calls)


def test_praw_handler():
    praw_handler = PrawHandler()
    for submission in praw_handler.stream_new_submissions("test", skip_existing=False):
        print(submission)
        assert submission.title
        assert submission.url
        assert submission.author
        assert submission.id
