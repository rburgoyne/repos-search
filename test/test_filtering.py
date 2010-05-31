#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import unittest
import tempfile
from subprocess import Popen
from subprocess import PIPE


class TestReposSearchIndexingFilter(unittest.TestCase):

  def testSomething(self):
    pass

# sample repository
def getTestrepo():
    dir = tempfile.mkdtemp()
    Popen(["svnadmin", "create", dir], stdout=PIPE).communicate()[0]
    Popen(["svnadmin", "load", dir], stdout=PIPE, stderr=PIPE, stdin=PIPE).communicate(testrepo1)[0]
    return dir

def cleanup(testrepoDir):
    # for now leave it
    #print testrepoDir
    pass

testrepo1 = """SVN-fs-dump-format-version: 2
"""

if __name__ == '__main__':
  ''' Run tests. If called with single argument "testrepo" load repo only. '''
  if len(sys.argv) > 1 and sys.argv[1] == 'testrepo':
    print "Testrepo loaded at: %s" % getTestrepo()
  else:
    repo = getTestrepo()
    unittest.main()
    cleanup(repo)
