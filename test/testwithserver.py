#!/usr/bin/env python

import unittest
import tempfile
import os
from subprocess import check_call
from shutil import rmtree, copyfile
import urllib2
from urllib import quote
import json

# global settings for the test
# currently assumes a manually started server
solr = 'http://localhost:8080/solr/'
repo = tempfile.mkdtemp()
reponame = os.path.basename(repo)
repourl = 'file://' + repo

def run(cmd):
  print '# ' + ' '.join(cmd)
  return check_call(cmd)

def createRepository():
  ''' create repository with indexing hook enabled '''
  run(['svnadmin', 'create', repo])
  hook = repo + '/hooks/post-commit'
  f = open(hook, 'w')
  f.write('#!/bin/sh\n')
  f.write('%s $1 $2\n' % os.path.abspath('../hook/svnhook.py'))
  f.close()
  os.chmod(hook, 0777)

def createInitialStructure():
  run(['svn', 'import', 'docs', repourl + '/misc', '-m', 'Mixed documents'])
  run(['svnlook', 'tree', repo])

def curl(url):
  # transparently restrict hits to this instance
  if url.find('q=') > 0:
    url = url + '&fq=id_repo:' + reponame
  r = urllib2.urlopen(url)
  return r.read()

def search(queryType, query):
  '''
  queryType: standard/None, meta, content
  query: solr escaped but not urlencoded query
  '''
  # todo encode and stuff
  r = curl(solr + 'svnhead/select?qt=' + queryType + '&q=' + quote(query) + '&wt=json')
  return json.loads(r)

def searchMeta(query):
  return search('meta', query)

def searchContent(query):
  return search('content', query)


class SvnhookTest(unittest.TestCase):
  
  def testServerIsUp(self):
    r = curl(solr + '')
    self.assertTrue(r.find('svnhead') > -1, r)
    
  def testFilename(self):
    r = searchMeta('shouldBeUNIQUEfilename')
    self.assertEqual(r['response']['numFound'], 1)
    self.assertEqual(r['response']['docs'][0]['id'], 
                     u'%s^/misc/filenames/shouldBeUniqueFilename.txt' % reponame)

  def testFilenameWithExtension(self):
    r = searchMeta('shouldbeuniquefilename.txt')
    self.assertEqual(r['response']['numFound'], 1)

  def testContentXslAndOds(self):
    r = searchContent('"cell B2"')
    self.assertEqual(r['response']['numFound'], 2)
    print r


if __name__ == '__main__':
  createRepository()
  createInitialStructure()
  unittest.main()
  rmtree(repo)