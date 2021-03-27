from plugins.subwatch.plugin import PrawHandler


def test_subwatch():
    praw_handler = PrawHandler()
    for url in praw_handler.stream_new_submissions("test"):
        print(url)
        assert url
