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
hook = repo + '/hooks/post-commit'
hooklog = hook + '.log'

def run(cmd):
  print '# ' + ' '.join(cmd)
  return check_call(cmd)

def createRepository():
  ''' create repository with indexing hook enabled '''
  run(['svnadmin', 'create', repo])
  hook = repo + '/hooks/post-commit'
  f = open(hook, 'w')
  f.write('#!/bin/sh\n')
  f.write('%s $1 $2' % os.path.abspath('../hook/svnhook.py'))
  f.write(' > %s 2>&1\n' % hooklog)
  f.close()
  os.chmod(hook, 0777)

def createInitialStructure():
  '''
    Test data can be added from tests but we do a batch first for faster test execution.
    All tests may use this data.
  '''
  print '# ------- setup start --------'
  run(['svn', 'import', 'docs', repourl + '/docs', '-m', 'Mixed documents'])
  # properties must be added in a working copy, using a small subfolder for performance
  propwc = tempfile.mkdtemp()
  run(['svn', 'co', repourl + '/docs/svnprops/', propwc])
  txt =  propwc + '/textwithsvnprops.txt'
  run(['svn', 'propset', 'svn:keywords', 'Id LastChangedRevision HeadURL', txt])
  # Currently keywords properties are only treated as keywords if their namespace match the schema copyField rule 
  run(['svn', 'propset', 'cms:keywords', 'ReposSearch repossearch keywordfromsvnprop', txt])
  run(['svn', 'propset', 'whatever:tags', 'metadataindexing tagging-in-svnprop', txt])
  run(['svn', 'propset', 'custom:someurl', 'Visit http://repossearch.com/', txt])
  run(['svn', 'status', propwc])
  run(['svn', 'commit', '-m', 'Properties added', propwc])
  print '# ------- common test data:'
  run(['svnlook', 'tree', repo])
  print '# ------- hook log:'
  f = open(hooklog, 'r')
  print f.read()
  f.close()
  print '# ------- setup done --------'
  print ''

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
  print '\n' + r 
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
                     u'%s^/docs/filenames/shouldBeUniqueFilename.txt' % reponame)

  def testFilenameWithExtension(self):
    r = searchMeta('shouldbeuniquefilename.txt')
    self.assertEqual(r['response']['numFound'], 1)

  def testContentXslAndOds(self):
    r = searchContent('"cell B2"')
    self.assertEqual(r['response']['numFound'], 2)
    
  def testSvnPropsTextfile(self):
    r = searchMeta('textwithsvnprops.txt')
    self.assertEqual(r['response']['numFound'], 1)
    self.assertEqual(r['response']['docs'][0]['svnrevision'], 2)
    self.assertFalse(r['response']['docs'][0].has_key('svnprop_svn_keywords'),
                     'svn properties should normally not be indexed');
    self.assertEqual(r['response']['docs'][0]['svnprop_custom_someurl'], 'Visit http://repossearch.com/',
                     'by default custom properties should be indexed and stored as plain strings')
    
  def testMetaDontMatchSvnKeywords(self):
    r = searchMeta('LastChangedRevision')
    self.assertEqual(r['response']['numFound'], 0,
                     'svn keywords should not be indexed because they are not keywords')
    
  def testSearchOnCustomKeywords(self):
    r = searchMeta('keywordfromsvnprop')
    self.assertEqual(r['response']['numFound'], 1)
    self.assertEqual(r['response']['docs'][0]['id'], 
                     '%s^/docs/svnprops/textwithsvnprops.txt' % reponame,
                     'meta search should include keywords properties with likely namespaces except svn')

  def testSearchOnCustomTagsField(self):
    r = searchMeta('tagging-in-svnprop')
    self.assertEqual(r['response']['numFound'], 1)
    self.assertEqual(r['response']['docs'][0]['id'], 
                     '%s^/docs/svnprops/textwithsvnprops.txt' % reponame,
                     'meta search should include any *:kewords property value except svn:keywords')    

if __name__ == '__main__':
  createRepository()
  createInitialStructure()
  unittest.main()
  rmtree(repo)