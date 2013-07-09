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

def authorize(user, repo, path):
    """
    Given a repository and a path, start with the full path, then work
    backwards, looking for a collection of rules that match it. At each step,
    assign the path to a reference that will eventually point to the correct
    collection of rules when it is found. This reduces the time repeating
    searches.

    Once a collection of rules that matches the path has been found, search it
    for a rule that matches the given user. If none is found, search for a
    rule that matches all users, and then a rule that matches any group the
    user is in. Once a rule is found, the rule is saved directly with the user
    name so that group and wildcard searches will not have to be attempted
    for that particular rule again.
    """ 
    path_rules = None
    path_rules_ptr = [None]
    # Remove trailing slashes from query path for consistency.
    path = path.rstrip('/')
    # First, check if a rule is defined for the specific path
    path_rules = rules.get(repo + ":" + path)
    if not path_rules:
        # Iterate over all parent paths in reverse
        path = path.lstrip('/')
        split_path = path.split('/')
        for parentpath_length in reversed(range(len(split_path))):
            parentpath = repo + ":/" + "/".join(split_path[0:parentpath_length])
            path_rules = rules.get(parentpath)
            if path_rules:
                path_rules_ptr[0] = path_rules[0]
                break
            else:
                rules[parentpath] = path_rules_ptr
    if not path_rules:
        # Get the rules for root 
        path_rules = rules.get('/')
    if path_rules:
        path_rules_ptr[0] = path_rules[0]
    else:
        # No rules are defined for the given path.
        rules['/'] = [None]
        return False

    if not path_rules[0]:
       return False
    authorized = path_rules[0].get(user)
    if authorized is None:
        for group in group_membership[user]:
            authorized = path_rules[0].get('@' + group)
            if authorized is not None:
                break
        if authorized is None:
            authorized = path_rules[0].get('*')
        if authorized is None:
            authorized = False
        path_rules[0][user] = authorized
    return authorized
