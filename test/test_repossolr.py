#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import sys
sys.path.append('../hook/')
from repossolr import *
from optparse import OptionParser

class ReposSolrTest(unittest.TestCase):
      
  def testGetDocId(self):
    opt = OptionParser().parse_args([])[0]
    opt.base = ''
    opt.prefix = ''
    s = ReposSolr(opt)
    self.assertEqual(s.getDocId('/file.txt', None), '^/file.txt')
    opt.base = 'b'
    self.assertEqual(s.getDocId( '/file.txt', None), 'b^/file.txt')
    opt.prefix = '/svn/'
    self.assertEqual(s.getDocId( '/file.txt', None), '/svn/b^/file.txt')
    self.assertEqual(s.getDocId( '/file.txt', 1234567), '/svn/b^/file.txt@1234567')
    opt.base = ''
    self.assertEqual(s.getDocId( '/file.txt', None), '/svn/^/file.txt')
 
if __name__ == '__main__':
  unittest.main()
           
