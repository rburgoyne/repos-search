
import pluginmanager
 
@pluginmanager.register("FOO_ACTIVE")
def print_data(*args, **kwargs):
    print repr(args)
    print repr(kwargs)
    if "data" in kwargs:
        print "Plugin system works. Got: %s" % kwargs["data"]
    else:
        print "Didn't receive any data."
        
pluginmanager.trigger_event("FOO_ACTIVE", 
                            data="this data is sent to the plugin", 
                            foo="so is this")
 