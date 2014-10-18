import logging
import inspect
import linecache

class PluginManager(object):
    """Keeps track of, loads, and unloads plugins."""

    iteration_counter = 0
    """Holds our current iteration point"""

    cardinal = None
    """Instance of CardinalBot"""

    plugins = {}
    """List of loaded plugins"""

    def __init__(self, cardinal, plugins=None):
        """Creates a new instance, optionally with a list of plugins to load

        Keyword arguments:
          cardinal -- An instance of CardinalBot to pass to plugins.
          plugins -- A list of plugins to be loaded when instanced.

        Raises:
          ValueError -- When plugins is not a list.

        """
        # To prevent circular dependencies, we can't sanity check this. Hope
        # for the best.
        self.cardinal = cardinal

        # Make sure we operate on a list
        if plugins is not None and not isinstance(plugins, list):
            raise ValueError("Plugins argument must be a list")

        for plugin in plugins:
            self.load_plugin(plugin)

    def __iter__(self):
        """Part of the iterator protocol, returns iterator object

        In this case, this will return itself as it keeps track of the iterator
        internally. Before returning itself, the iteration counter will be
        reset to 0.

        Returns:
          PluginManager -- Returns the current instance.

        """
        # Reset the iteration counter
        self.iteration_counter = 0

        return self

    def next(self):
        """Part of the iterator protocol, returns the next plugin

        Returns:
          dict -- Dictionary containing a plugin's data.

        Raises:
          StopIteration -- Raised when there are no plugins left.

        """
        # Make sure we have the dictionary sorted so we return the proper
        # element
        keys = sorted(self.plugins.keys())

        # Increment the counter
        self.iteration_counter += 1

        # Make sure that the 
        if self.iteration_counter > len(keys):
            raise StopIteration

        return self.plugins[keys[self.iteration_counter - 1]]

    def _import_module(self, module, type='plugin'):
        """Given a plugin name, will import it from its directory or reload it

        If we are passing in a module, we can safely assume at this point that
        it's a plugin we've already loaded, so we just need to run reload() on
        it. However, if we're loading it fresh then we need to import it out
        of the plugins directory.

        Returns:
          object -- The module that was loaded.

        """
        if inspect.ismodule(module):
            return reload(module)
        elif isinstance(module, basestring):
            return importlib.import_module('plugins.%s.%s' % (module, type))

    def _create_plugin_instance(self, module):
        """Creates an instance of the plugin module

        If the setup() function of the plugin's module takes an argument then
        we will provide the instance of CardinalBot to the plugin.

        Keyword arguments:
          module -- The module to instantiate.

        Returns:
          object -- The instance of the plugin.

        Raises:
          ValueError -- When a plugin's setup function has more than one
            argument.
        """
        # Check whether the setup method on the module accepts an argument. If
        # it does, they are expecting our instance of CardinalBot to be passed
        # in. If not, just call setup. If there is more than one argument
        # accepted, the method is invalid.
        argspec = inspect.getargspec(module.setup)
        if len(argspec.args) == 0:
            instance = module.setup()
        elif len(argspec.args) == 1:
            instance = module.setup(self.cardinal)
        else:
            # TODO: Create an internal exception type for our own plugin rules.
            raise ValueError("Plugin setup function may not have more than "
                "one argument")

        return instance

    def _close_plugin_instance(self, plugin):
        """Calls the close method on an instance of a plugin

        If the plugin's module has a close() function, we will check whether
        it expects an instance of CardinalBot or not by checking whether it
        accepts an argument or not. If it does, we will pass in the instance of
        CardinalBot. This method is called just prior to removing the internal
        reference to the plugin's instance.

        Keyword arguments:
          plugin -- The name of the plugin to remove the instance of.

        Raises:
          ValueError -- When a plugin's close function has more than one
            argument.
        """

        instance = self.plugins[plugin]['instance']
        module = self.plugins[plugin]['module']

        if hasattr(instance, 'close') and inspect.ismethod(instance.close):
            # The plugin has a close method, so we now need to check how
            # many arguments the method has. If it only has one, then the
            # argument must be 'self' and therefore they aren't expecting
            # us to pass in an instance of CardinalBot. If there are two
            # arguments, they expect CardinalBot. Anything else is invalid.
            argspec = inspect.getargspec(
                sinstance.close
            )

            if len(argspec.args) == 1:
                module.close()
            elif len(argspec.args) == 2:
                module.close(self.cardinal)
            else:
            # TODO: Create an internal exception type for our own plugin rules.
            raise ValueError("Plugin close function may not have more than "
                "one argument")

    def _get_plugin_commands(self, instance):
        """Find the commands in a plugin and return them as callables

        Keyword arguments:
          instance -- An instance of a plugin.

        Returns:
          list -- A list of callable commands.

        """
        commands = []

        # Loop through each method on the instance, checking whether it's a
        # method meant to be interpreted as a command or not.
        for method in dir(instance):
            method = getattr(instance, method)

            if callable(method) and (hasattr(method, 'regex') or
                                     hasattr(method, 'commands'):
                # Since this method has either the 'regex' or the 'commands'
                # attribute assigned, it's registered as a command for
                # Cardinal.
                commands.append(method)

        return commands

    def _get_plugin_events(self, instance):
        """Find the events in a plugin and return them as callables

        Valid events are as follows:
          on_join   -- When a user joins a channel.
          on_part   -- When a user parts a channel.
          on_kick   -- When a user is kicked from a channel.
          on_invite -- When a user invites another user to a channel.
          on_quit   -- When a user quits a channel.
          on_nick   -- When a user changes their nick.
          on_topic  -- When a user sets the topic of a channel.
          on_action -- When a user performs an ACTION on a channel.

        Keyword arguments:
          instance -- An instance of a plugin.

        Returns:
          list -- A list of callable events.

        """
        events = []

        for method in dir(instance):
            method = getattr(instance, method)
            if callable(method) and (hasattr(method, 'on_join') or hasattr(method, 'on_part') or
                                     hasattr(method, 'on_quit') or hasattr(method, 'on_kick') or
                                     hasattr(method, 'on_action') or hasattr(method, 'on_topic') or
                                     hasattr(method, 'on_nick') or hasattr(method, 'on_invite')):
                events.append(method)

        return events

    def load(self, plugins):
        """Takes either a plugin name or a list of plugins and loads them.

        This involves attempting to import the plugin's module, import the
        plugin's config module, instance the plugin's object, and finding its
        commands and events.

        Keyword arguments:
          plugins -- This can be either a single or list of plugin names.

        Returns:
          list -- A list of failed plugins, or an empty list.

        Raises:
          ValueError -- When the `plugin` argument is not a string or list.

        """
        # If they passed in a string, convert it to a list (and encode the
        # name as UTF-8.)
        if isinstance(plugins, basestring):
            plugins = [plugins.encode('utf-8')]
        if not isinstance(plugins, list):
            raise ValueError(
                "Plugins argument must be a string or list of plugins"
            )

        # We'll keep track of plugins we failed to load (either because we)
        failed_plugins = []

        # Sort of a hack... this helps with debugging, as uncaught exceptions
        # can show the wrong data (line numbers / relevant code) if linecache
        # doesn't get cleared when a module is reloaded. This is Python's
        # internal cache of code files and line numbers.
        linecache.clearcache()

        for plugin in plugins:
            logging.info("Attempting to load plugin: %s" % plugin)

            # Import each plugin's module with our own hacky function to reload
            # modules that have already been imported previously
            try:
                if plugin in self.plugins:
                    logging.info("Already loaded, reloading: %s" % plugin)
                    module_to_import = self.plugins[plugin]['module']
                else:
                    module_to_import = plugin

                module = self._import_module(module_to_import)

            except Exception, e:
                # Probably a syntax error in the plugin, log the exception
                logging.exception("Could not load plugin module: %s" % plugin)
                failed_plugins.append(plugin)

                continue

            # Attempt to load the config file for the given plugin.
            #
            # TODO: Change this to use ConfigParser
            config = None
            try:
                if plugin in self.plugins and 'config' in self.plugins[plugin]:
                    config = self._import_module(
                        self.plugins[plugin]['config'], 'config'
                    )
                else:
                    config = self._import_module(
                        plugin, 'config'
                    )
            except ImportError:
                # This is expected if the plugin doesn't have a config file
                logging.info("No config found for plugin: %s" % plugin)
            except Exception, e:
                # This is probably due to a syntax error, so log the exception
                logging.exception("Could not load plugin config: %s" % plugin)

            # Instance the plugin
            try:
                instance = self._create_plugin_instance(module)
            except Exception, e:
                logging.exception("Could not instantiate plugin: %s" % plugin)
                failed_plugins.append(plugin)

                continue

            commands = self._get_plugin_commands(instance)
            events = self._get_plugin_events(instance)

            if plugin in self.plugins:
                self.unload(plugin)

            self.plugins[plugin] = {
                'module': module,
                'instance': instance,
                'commands': commands,
                'events': events
            }

            logging.info("Plugin %s successfully loaded" % plugin)

        return failed_plugins

    def unload(self, plugins):
        """Takes either a plugin name or a list of plugins and unloads them.

        Simply validates whether we have loaded a plugin by a given name, and
        if so, clears all the data associated with it.

        Keyword arguments:
          plugins -- This can be either a single or list of plugin names.

        Returns:
          list -- A list of failed plugins, or an empty list.

        Raises:
          ValueError -- When the `plugins` argument is not a string or list.

        """
        # If they passed in a string, convert it to a list (and encode the
        # name as UTF-8.)
        if isinstance(plugins, basestring):
            plugins = [plugins.encode('utf-8')]
        if not isinstance(plugins, list):
            raise ValueError("Plugins must be a string or list of plugins")

        # We'll keep track of any plugins we failed to unload (either because
        # we have no record of them being loaded or because the method was
        # invalid.)
        failed_plugins = []

        for plugin in plugins:
            logging.info("Attempting to unload plugin: %s" % plugin)

            if plugin not in self.plugins:
                logging.warning("Plugin was never loaded: %s" % plugin)
                failed_plugins.append(plugin)
                continue

                try:
                    self._close_plugin_instance(plugin)
                except Exception, e:
                    # Log the exception that came from trying to unload the
                    # plugin, but don't skip over the plugin. We'll still
                    # unload it.
                    logging.exception(
                        "Didn't close plugin cleanly: %s" % plugin
                    )
                    failed_plugins.append(plugin)

            # Once all references of the plugin have been removed, Python will
            # eventually do garbage collection. We only opened it in one
            # location, so we'll get rid of that now.
            del self.plugins[plugin]

        return failed_plugins