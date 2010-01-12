#!/usr/bin/env python
""" 
   Copyright 2009 Staffan Olsson repossearch.com

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
   
Index all revisions in a repository 
(c) Staffan Olsson repossearch.com
$LastChangedRevision$
"""

from optparse import OptionParser
import os
import sys
from subprocess import Popen, PIPE

usage = """Usage: python rebuild_index.py --indexer=svnhook.py -p REPO_PATH"""

parser = OptionParser(usage)
# all arguments will be forwarded to the indexer, except -i
parser.add_option("", "--indexer", dest="indexer", default="svnhook.py",
                  help="Execution path to the indexing script. "
                  + "Optional but if set it must be the first argument. Default: %default")
parser.add_option("-p", "--repository", dest="repo",
                  help="Local repository path")

if len(sys.argv) < 2:
  parser.print_help()
  sys.exit(2)

# special treatment in order to keep arguments for indexer
# found no option in OptonParser to let unknown arguments through
keepargs = sys.argv[1:]
a = 1
if sys.argv[a].startswith("--indexer="):
  keepargs = keepargs[1:]
  a = a + 1
if sys.argv[a] == "-p":
  a = a + 1
(options, args) = parser.parse_args(sys.argv[0:a+1])

if options.repo is None:
  parser.print_help()
  sys.exit(2)

def run(command):
  print('# ' + command)
  result = os.system(command)
  return result

look = Popen(['svnlook', 'youngest', options.repo], stdout=PIPE).communicate()[0]
youngest = int(look)
if not youngest:
  raise NameError('invalid repository %s, svnlook youngest retunred %d' % (options.repo, youngest))
print '# Latest revision is %d' % youngest

# TODO performance would be better if commit is done for example every 100 submit
# and optimize is done at the end

run('python %s -o drop %s' % (options.indexer, " ".join(keepargs)))

for i in range(1, youngest + 1):
  result = run('python %s -o batch -r %d %s' % (options.indexer, i, " ".join(keepargs)))
  if result > 0:
    raise NameError('Got exit code %d for command; %s' % (result, cmd))
    break

run('python %s -o commit %s' % (options.indexer, " ".join(keepargs)))
