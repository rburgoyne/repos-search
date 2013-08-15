"""
Read the authz file and provide methods for authorizing user access to a path.
"""

import ConfigParser
from collections import defaultdict

rules = {}
group_membership = defaultdict(list)

def read(authz_file):
    """
    Read the authz file using the ConfigParser module. The authz file consists
    of several sections. One of them is the "groups" section. Each item in the
    "groups" section is a group name mapped to a comma-delimited list of user
    names. The rest of the sections are path names. Each item in these sections
    is a user name, group name (prefixed by "@"), or "*" mapped to a set of
    permissions ("", "r", or "rw"). Subversion also allows for a "~" prefix to
    indicate a negated rule, but this is not currently implemented. Invert the
    group mapping so that given a specific user, all groups of which that user
    is a member can be obtained. Currently, this module only authorizes for
    reading, so map each path and user to True (the user has authorization to
    read the path), or False (not).

    @type  authz_file: string
    @param authz_file: The absolute or relative path to the Subversion authz file.
    """
    parser = ConfigParser.RawConfigParser()
    parser.optionxform = str

    try:
        parser.read(authz_file)
    except IOError:
        raise
    except ConfigParser.Error:
        raise

    for section in parser.sections():
        if section == 'groups':
            for item in parser.items(section):
                group_name = item[0]
                group_members = [member_name.strip() for member_name in item[1].split(',')]
                for group_member in group_members:
                    group_membership[group_member].append(group_name)
        else:
            # The section is a path. If it is not the root of a repository, 
            # remove any trailing slashes for consistency.
            if len(section) > 1 and section[-2] is not ':':
                path = section.rstrip('/')
            else:
               path = section
            path_rules = {}
            for item in parser.items(section):
                name = item[0]
                permissions = item[1]
                authorized = 'r' in item[1]
                path_rules[name] = authorized 
            # Each rule is actually a single-item list pointing to a rule
            # dictionary. This way, the following assignment produces the
            # desired results:
            # 
            #     rules_path_ptr = [None]
            #     rules[path1] = rules_path_ptr
            #     print rules[path1][0]
            #         None
            #     rules_path_ptr[0] = {"user1":True, "user2":False}
            #     print rules[path1][0]
            #         {"user1":True, "user2":False}
            #
            # Without being enclosed in a list, it wouldn't work:
            #
            #     rules_path_ptr = None
            #     rules[path1] = rules_path_ptr
            #     print rules[path1]
            #         None
            #     rules_path_ptr = {"user1":True, "user2":False}
            #     print rules[path1]
            #         None
            #
            # Putting the object in a list is essentially like using a pointer
            # in C++ to assign by reference.
            rules[path] = [path_rules]

def authorize(user, repo, path, path_rules_ptr=None):
    """
    Given a repository and a path, start with the full path, then work
    backwards, looking for a collection of rules that match it. At each step,
    assign the path to a reference that will eventually point to the correct
    collection of rules when it is found. This reduces the time repeating
    searches.

    Once a collection of rules that matches the path has been found, search it
    for a rule that matches the given user. If none is found, search for a rule
    that matches any group the user is in, and then a rule that matches all 
    users. Once a rule is found, the rule is saved directly with the user
    name so that group and wildcard searches will not have to be attempted
    for that particular rule again.

    @type  user:           string
    @param user:           The username of the user to be authorized.
    @type  repo:           string
    @param repo:           The repository where the requested file is located.
    @type  path:           string
    @param path:           The path to the requested file.
    @type  path_rules_ptr: list of dictionaries
    @param path_rules_ptr: A single-element list containing a dictionary describing
                           the rules for the requested file. When the function is
                           called externally, this should be `None`. When it is
                           called recursively, this parameter is used to maintain the
                           pointer.
    @rtype:                boolean
    @return:               True if the user is authorized to read the requested file,
                           False otherwise.
    """
    if not path_rules_ptr:
        path_rules_ptr = [None]
    # Remove trailing slashes from query path for consistency.
    path = path.rstrip('/')
    # Full paths are of the form `Repo:/path/to/file`, `Repo:/` for empty paths, or
    # `/` for the root
    fullpath = ""
    if repo:
        if path:
            fullpath = repo + ":" + path
        else:
            fullpath = repo + ":/"
    else:
        fullpath = "/"
    path_rules = rules.get(fullpath)
    if path_rules:
        # Set the pointer to point to the rules for this path. Previously traversed
        # subdirectories and files with empty rule sets will have their rules set to 
        # these rules.
        path_rules_ptr[0] = path_rules[0]
        authorized = path_rules[0].get(user)
        if authorized is None:
            for group in group_membership[user]:
                authorized = path_rules[0].get('@' + group)
                if authorized is not None:
                    break
            if authorized is None:
                authorized = path_rules[0].get('*')
            if authorized is not None:
                # This will cache a rule for the user, so that future lookups do not
                # need so search groups or the wildcard.
                path_rules[0][user] = authorized
        if authorized is not None:
            return authorized
    else:
        # This creates a cache for the rules for this path. When the recursive
        # function finally returns, `path_rules_ptr` will be set, and future lookups
        # on this path will be able to return without continuing the recursion.
        rules[fullpath] = path_rules_ptr
    if not repo:
        # This is the base case.
        return False
    if not path:
        # The path has been reduced to nothing, so perform one more recursion to
        # examine the root.
        repo = ""
    # Remove the last item in the path and try again.
    return authorize(user, repo, path[0:path.rfind("/")], path_rules_ptr)
