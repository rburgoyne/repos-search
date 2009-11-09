# pluginmanager.py
# http://www.evanfosmark.com/2009/07/simple-event-driven-plugin-system-in-python/
from collections import defaultdict
import os
 
plugins = defaultdict(list)
def register(*events):
    """ This decorator is to be used for registering a function as a plugin for
        a specific event or list of events. 
    """
    def registered_plugin(funct):
        for event in events:
            plugins[event].append(funct)
        return funct
    return registered_plugin
 
def trigger_event(event, *args, **kwargs):
    """ Call this function to trigger an event. It will run any plugins that
        have registered themselves to the event. Any additional arguments or
        keyword arguments you pass in will be passed to the plugins.
    """
    for plugin in plugins[event]:
        plugin(*args, **kwargs)
 
def load_handlers():
    """ Loads python files with "handle" in name as plugin modules """
    folder = os.path.dirname(__file__)
    for filename in os.listdir(folder):
        # Ignore subfolders
        if os.path.isdir(os.path.join(folder, filename)):
            continue
        (mod, ext) = os.path.splitext(filename)
        if ext != '.py' or mod.find('handle') == -1:
            continue
        __import__(mod, globals(), locals(), [], -1)

""" Automatically load handlers """
load_handlers()
