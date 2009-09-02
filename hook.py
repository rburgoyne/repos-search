#!/usr/bin/env python
"""Fulltext indexing of committed files.
(c) Staffan Olsson reposstyle.com
Requires Solr 1.4-dev example set up as described in:
http://wiki.apache.org/solr/ExtractingRequestHandler
$LastChangedRevision$
"""

import logging
import logging.handlers
import os
from optparse import OptionParser
from subprocess import Popen
from subprocess import PIPE
import re
from tempfile import NamedTemporaryFile
from urllib import urlencode

""" hook options """
parser = OptionParser()
parser.add_option("-p", "--repository", dest="repo",
    help="A local repository path")
parser.add_option("", "--nobase", dest="nobase", action='store_true', default=False,
    help="Set to false to disable indexing of paths prefixed with repo name (i.e. @base)."
        + " If the index is not for SVNParentPath repsitories, this makes paths easier to read.")
parser.add_option("-r", "--revision", dest="rev",
    help="Committed revision")
parser.add_option("", "--loglevel", dest="loglevel", default="info",
    help="The loglevel (standard Log4J levels, lowercase). Defaults to %default.")
parser.add_option("", "--cloglevel", dest="cloglevel", default="info",
    help="The console loglevel (standard Log4J levels, lowercase). Defaults to %default.")
parser.add_option("", "--svnlook", dest="svnlook", default="/usr/bin/svnlook",
    help="The svnlook command, default: %default")
parser.add_option("", "--curl", dest="curl", default="/usr/bin/curl",
    help="The curl command, default: %default")
parser.add_option("", "--solr", dest="solr", default="http://localhost:8983/solr/",
    help="Solr host, port and schema. Default: %default")

""" global variables """
(options, args) = parser.parse_args()
if options.repo is None:
    parser.print_help()
    sys.exit(2)

""" set up logger """
LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}
level = LEVELS.get(options.loglevel)
if not level:
    raise NameError("Invalid log level %s" % options.loglevel)
logger = logging.getLogger("Repos Search hook")
logger.setLevel(level)
# console
ch = logging.StreamHandler()
ch.setLevel(level)
ch.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(ch)


def submitDelete(path):
    logger.warn('Delete not implemented. File %s will remain in search index.' % path)

def submitContents(path):
    """path could be a folder so we should handle that"""

    params = {"literal.id": path, "commit": "true"}
    # path should begin with slash so that base can be prepended
    # this means that for indexes containing repo name paths do not begin with slash 
    if base:
        params["literal.id"] = base + params["literal.id"]

    cat = NamedTemporaryFile('wb')
    logger.debug("Writing %s to temp %s" % (path, cat.name))    
    catp = Popen([options.svnlook, "cat", "-r %d" % rev, repo, path], stdout=cat)
    catp.communicate()
    if not catp.returncode is 0:
        logger.debug("Cat failed for %s. It must be a folder." % (path))
        return

    # post contents with curl as in solr example
    cat.flush()
    curl = options.curl
    if logger.getEffectiveLevel() is logging.DEBUG:
        curl = curl + " -v"
    result = os.system("%s '%supdate/extract?%s' -F 'myfile=@%s'"
              % (curl, options.solr, urlencode(params), cat.name))
    if result:
        raise NameError("Failed to submit document to index, got %d" % result)
    cat.close()
    logger.info("Successfully indexed id: %s" % params["literal.id"]);


""" set up repository connection """
repo = options.repo.rstrip("/")
base = None
if not options.nobase:
    base = os.path.basename(repo)
rev = long(options.rev)
logger.info("Repository '%s' base '%s' rev %d" % (repo, base, rev))

changedp = Popen([options.svnlook, "changed", "-r %d" % rev, repo], stdout=PIPE)
changed = changedp.communicate()[0]

""" read changes """
changematch = re.compile(r"^([ADU_])([U\s])\s+(.+)$")
for change in changed.splitlines():
    m = changematch.match(change);
    c = m.group(1)
    p = "/" + m.group(3)
    logger.debug("%s%s  %s" % m.groups())
    if c is "D":
        submitDelete(p)
        continue
    if c is "A" or "U":
        submitContents(p)
    
