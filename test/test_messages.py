#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import time
# using solrpy
import solr

solrUrl = 'http://localhost:8080/solr/'

class TestReposSearchIndexingFilter(unittest.TestCase):
  
  def testPostMessage(self):
    testid = "%d" % time.time()
    s = solr.SolrConnection(solrUrl + 'messages')

    s.add(source='Repos Search test ' + testid, category='test message', body="the\nmessage\nbody")
    s.commit()

    response = s.query('source:"Repos Search test %s"' % testid) # in real
    self.assertEqual(response.results.numFound, '1')
    hit = response.results[0]
    self.assertEqual(hit['category'], 'test message')
    self.assertEqual(hit['body'], 'the\nmessage\nbody')
    self
    pass
  
  
if __name__ == '__main__':
  unittest.main()