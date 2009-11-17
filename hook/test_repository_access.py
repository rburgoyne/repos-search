#!/usr/bin/env python

import unittest
from svnhook import proplistToDict

class SvnhookTest(unittest.TestCase):
    
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
        self.assertEqual(p['svn:executable'], '')
        self.assertEqual(p['what:Ever'], 'jell o')
 
if __name__ == '__main__':
    unittest.main()
           