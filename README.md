# Fork of Cardinal for a subwatch replacement.

Run:
```
docker run --env-file .env -v $(pwd)/config:/usr/src/app/config ghcr.io/lolei/nuh_bot:1.0.0 config/config.json
```

Original readme below.

[![Cardinal](./_assets/cardinal.svg)](https://github.com/JohnMaguire/Cardinal)

# Meet Cardinal.

[![Build Status](https://github.com/JohnMaguire/Cardinal/workflows/Cardinal/badge.svg)](https://github.com/JohnMaguire/Cardinal/actions?query=workflow%3ACardinal) [![Coverage Status](https://codecov.io/github/JohnMaguire/Cardinal/coverage.svg?branch=master)](https://codecov.io/github/JohnMaguire/Cardinal?branch=master)

Cardinal is a Python Twisted IRC bot with a focus on ease of development. It features reloadable asynchronous plugins, [Python decorators for commands](https://github.com/JohnMaguire/Cardinal/wiki/Writing-Plugins#adding-commands-to-a-plugin) and [IRC events](https://github.com/JohnMaguire/Cardinal/wiki/Cardinal-Events), [simple persistent JSON data storage](https://github.com/JohnMaguire/Cardinal/wiki/Database-Access), and [a well-documented API](https://github.com/JohnMaguire/Cardinal/wiki/Cardinal-Methods).

You can join [#cardinal](https://www.mibbit.com/#cardinal@irc.darkscience.net:+6697) on the [DarkScience](http://www.darkscience.net/) IRC network for questions or support. (irc.darkscience.net/+6697 &mdash; SSL required)

## What can Cardinal do?

Anything, if you're creative! Cardinal does come with some plugins to get you started...

* Fetching URL titles
* Wolfram Alpha calculations
* Wikipedia definitions
* Urban Dictionary definitions
* Movie and TV show lookups
* Weather reports
* Reminders
* Google searches
* Now playing w/ Last.fm
* Stock ticker
* sed-like substitutions
* ... and more!

But the best part of Cardinal is how easy it is to add more!

## Basic Usage

### Configuration

1. Copy the `config/config.example.json` file to `config/config.json` (you can use another filename as well, such as `config.freenode.json` if you plan to run Cardinal on multiple networks).

2. Copy `plugins/admin/config.example.json` to `plugins/admin/config.json` and add your `nick` and `vhost` in order to take advantage of admin-only commands (such as reloading plugins, telling Cardinal to join a channel, or blacklisting plugins within a channel).

### Running

Cardinal is run via Docker. To get started, install [Docker](https://docs.docker.com/install/) and [docker-compose](https://docs.docker.com/compose/install/).

If your config file is named something other than `config/config.json`, you will need to create a `docker-compose.override.yml` file like so:

```yaml
version: "2.1"
services:
    cardinal:
        command: config/config_file_name.json
```

To start Cardinal, run `docker-compose up -d`. To restart Cardinal, run `docker-compose restart`. To stop Cardinal, run `docker-compose down`.

## Writing Plugins

Cardinal was designed with ease of development in mind.

```python
from cardinal.decorators import command, help

class HelloWorldPlugin:
    @command(['hello', 'hi'])
    @help("Responds to the user with a greeting.")
    @help("Syntax: .hello")
    def hello(self, cardinal, user, channel, msg):
        nick, ident, vhost = user
        cardinal.sendMsg(channel, "Hello {}!".format(nick))

entrypoint = HelloWorldPlugin
```

Cardinal also offers a [lightweight database API](https://github.com/JohnMaguire/Cardinal/wiki/Database-Access). [Visit the wiki](https://github.com/JohnMaguire/Cardinal/wiki/Writing-Plugins) for detailed information.

## Contributing

Cardinal is a public, open-source project, licensed under the [MIT License](LICENSE). Anyone may contribute.

When submitting a pull request, you may add your name to the [CONTRIBUTORS](CONTRIBUTORS) file.
