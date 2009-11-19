#!/usr/bin/env python

import unittest
from svnhook import *
from optparse import OptionParser

class SvnhookTest(unittest.TestCase):
    
    def testGetOptions(self):
        # use the global parser
        (opt, args) = parser.parse_args(['-p', '/svn/r1/'])
        self.assertEquals(opt.repo, '/svn/r1/')
        self.assertEquals(opt.nobase, False, 'default')
    
    def testPreprocessOptions(self):
        opt = OptionParser().parse_args()[0]
        opt.repo = '/svn/r1/'
        opt.rev = '1234'
        opt.nobase = False
        optionsPreprocess(opt)
        self.assertEqual(opt.repo, '/svn/r1', 'should strip trailing space from repo')
        self.assertEqual(opt.rev, 1234, 'should make rev numeric')
        self.assertEqual(opt.base, 'r1', 'should get base from last folder name in repo path')
        pass
    
    def testGetProplist(self):
        pass
    
    def testProplistToDict(self):
        xml = '''<?xml version="1.0"?>
            <properties>
            <target
               path="reb.py">
            <property
               name="svn:executable"></property>
            <property
               name="what:Ever">jell o</property>
            </target>
            </properties>
            '''
        p = proplistToDict(xml)
        self.assertFalse(p['svn:executable'])
        self.assertEqual(p['svn:executable'], '')
        self.assertEqual(p['what:Ever'], 'jell o')
 
if __name__ == '__main__':
    unittest.main()
           