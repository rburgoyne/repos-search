#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import tempfile
import os
from subprocess import check_call
from shutil import rmtree, copyfile
import urllib2
from urllib import quote
import json
import re
import shutil

# global settings for the test
# currently assumes a manually started server
solr = 'http://localhost:8080/solr/'
repo = tempfile.mkdtemp()
reponame = os.path.basename(repo)
repourl = 'file://' + repo
hook = repo + '/hooks/post-commit'
hooklog = hook + '.log'

def run(cmd):
  #not properly quoted:#print '# ' + ' '.join(cmd)
  return check_call(cmd)

def createRepository():
  ''' create repository with indexing hook enabled '''
  run(['svnadmin', 'create', repo])
  hook = repo + '/hooks/post-commit'
  f = open(hook, 'w')
  f.write('#!/bin/sh\n')
  f.write('export LC_ALL="en_US.UTF-8"\n')
  f.write('%s $1 $2' % os.path.abspath('../hook/svnhook.py'))
  f.write(' >> %s 2>&1\n' % hooklog)
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
  txt = propwc + '/textwithsvnprops.txt'
  run(['svn', 'propset', 'svn:keywords', 'Id LastChangedRevision HeadURL', txt])
  # Currently keywords properties are only treated as keywords if their namespace match the schema copyField rule 
  run(['svn', 'propset', 'cms:keywords', 'ReposSearch repossearch keywordfromsvnprop 600K', txt])
  run(['svn', 'propset', 'whatever:tags', 'metadataindexing tagging-in-svnprop', txt])
  run(['svn', 'propset', 'custom:someurl', 'Visit http://repossearch.com/', txt])
  run(['svn', 'propset', 'svn:mime-type', 'application/pdf', propwc + '/shortpdf.pdf'])
  run(['svn', 'propset', 'cms:keywords', 'keywordfromsvnprop', propwc + '/shortpdf.pdf'])
  run(['svn', 'propset', 'custom:doc-title', 'SvnpropDocTitle with dash convention', propwc + '/shortpdf.pdf'])
  run(['svn', 'propset', 'custom:title', 'SvnpropTitle in addition to embedded', propwc + '/shortpdf.pdf'])
  # need to test that the server supports long query strings
  (bigprop, bigpropf) = tempfile.mkstemp()
  os.write(bigprop, 'a' * 30720) # 30k, we should expect servers to allow 32 k header size
  os.close(bigprop)
  run(['svn', 'propset', 'custom:big', '-F', bigpropf, propwc + '/longpropertyvalue.txt'])
  os.remove(bigpropf)
  # creating the invalid xml here so the error is not logged in rev 1 too
  xml = propwc + '/invalid, tag not closed.xml'
  f = open(xml, 'w')
  f.write('<?xml version="1.0"?>\n<document>\n<opentag>\n</document>\n')
  f.close()
  run(['svn', 'add', xml])
  run(['svn', 'propset', 'some:prop', 'OnInvalidXml', xml])
  run(['svn', 'commit', '-m', 'Properties added', propwc])
  # making a folder copy of a trunk folder to test handling
  codewc = tempfile.mkdtemp()
  run(['svn', 'co', repourl + '/docs/codeproject/', codewc])
  run(['svn', 'cp', codewc + '/trunk', codewc + '/branches/1.0.x'])
  run(['svn', 'commit', '-m', 'Branched a codeproject', codewc])
  print '# ---- common test data ----'
  run(['svnlook', 'tree', repo])
  print '# ------- hook log ---------'
  f = open(hooklog, 'r')
  print f.read()
  f.close()
  print '# Hook log path: %s' % hooklog
  print '# ------- setup done --------'
  print ''

def curl(url):
  # transparently restrict hits to this instance
  if url.find('q=') > 0:
    url = url + '&fq=id_repo:' + reponame
  r = urllib2.urlopen(url)
  return r.read()

def search(query, queryType='standard', schema='svnhead', sort='id asc'):
  '''
  queryType: standard/None, meta, content
  query: solr escaped but not urlencoded query
  sort: on id for predictable result ordering, set to empty to test ranking
  '''
  # todo encode and stuff
  r = curl(solr + schema + '/select?qt=' + queryType + '&q=' + quote(query) + '&wt=json&sort=' + quote(sort))
  #print '\n' + r 
  return json.loads(r)

def searchMeta(query):
  return search(query, 'meta')

def searchContent(query):
  return search(query, 'content')

def s1(queryType, query):
  ''' search, throw exception if number if hits is not 1, return the document id for the hit '''
  r = search(query, queryType)
  n = r['response']['numFound']
  if n == 0:
    raise NameError('No results for query "%s" type %s' % (query, queryType))
  if n > 1:
    raise NameError('%d results for query "%s" type %s: \n%s' % (n, query, queryType, repr(r)))
  return r['response']['docs'][0]['id'].partition('^')[2]

class ReposSearchTest(unittest.TestCase):
  
  def testServerIsUp(self):
    r = curl(solr + '')
    self.assertTrue(r.find('svnhead') > -1, r)
  
  def testRepo(self):
    # tests query tokenizer on repo field, implicit OR, don't know if this is a feature
    r = search('id_repo:(repo1 %s repo2)' % reponame)
    self.assertTrue(r['response']['numFound'] > 0)
    
  def testFilename(self):
    self.assertEqual(s1('meta', 'shouldBeUNIQUEfilename'), 
                     '/docs/filenames/shouldBeUniqueFilename.txt')

  def testDerivedFieldSearch(self):
    r = search('name:shouldBeUniqueFilename.txt')
    self.assertEqual(r['response']['numFound'], 1)
    r = search('name:shouldBeUniqueFilename.txt AND extension:txt')
    self.assertEqual(r['response']['numFound'], 1)
    r = search('folder:/docs/filenames/')
    self.assertTrue(r['response']['numFound'] > 0)
    r = search('folder:"/docs/filenames"')
    self.assertEqual(r['response']['numFound'], 0, 'should not match if the trailing slash is not there') # or can we match both?
    r = search('folder:"/docs/images/howto screenshots/"')
    self.assertTrue(r['response']['numFound'] > 0, 'should match folder with whitespace')

  def testFilenameWithExtension(self):
    self.assertEqual(s1('meta', 'shouldbeuniquefilename.txt'), 
                     '/docs/filenames/shouldBeUniqueFilename.txt')
    
  def testFilenameTokenizeDash(self):
    self.assertEqual(s1('standard', 'name:(subversion AND related AND document2)'), 
                     '/docs/filenames/Subversion-related Document2, 2010-02-10.txt',
                     'dash should be searchable as space')
    # How do we handle dashes when the adjacent chars are digits?
    self.assertEqual(s1('meta', 'subversion document 2010'), 
                     '/docs/filenames/Subversion-related Document2, 2010-02-10.txt')    
    self.assertEqual(s1('meta', '2010-02-10'), 
                     '/docs/filenames/Subversion-related Document2, 2010-02-10.txt') 
    # TODO Should dash-separated words be joined? Difference between digits and letters?
    #self.assertEqual(s1('meta', '20100210'), 
    #                 '/docs/filenames/Subversion-related Document2, 2010-02-10.txt')
    #self.assertEqual(s1('meta', 'subversionrelated 2010-02-10'), 
    #                 '/docs/filenames/Subversion-related Document2, 2010-02-10.txt')          
    # TODO Should CamelCase be split into separate words? in that case we should have 2 hits above
    # Even if CamelCase is split it must still match as one word, as below
    self.assertEqual(s1('meta', 'subversionrelated ver'), 
                     '/docs/filenames/SubversionRelated DNR333 ver 11.2.txt')    
  
  def testFilenameTokenizerCodes(self):
    self.assertEqual(s1('meta', '11.2'), 
                     '/docs/filenames/SubversionRelated DNR333 ver 11.2.txt',
                     'string like 11.2 (version number) must be searchable')
    self.assertEqual(s1('meta', 'DNR333'), 
                     '/docs/filenames/SubversionRelated DNR333 ver 11.2.txt',
                     'letters+digits could be a product code and must be searchable')
  
  def testFilenameLatin1Accents(self):
    self.assertEqual(s1('meta', 'aeea'),
                     u'/docs/filenames/Latin1 accents áéèà.txt',
                     'accented chars should be searchable without accent')
  
  def testFilenameTokenizeWhitespaceComma(self):
    self.assertEqual(s1('standard', 'name:(short AND not AND long AND filename AND txt)'),
                     '/docs/filenames/short, not long, filename.txt',
                     'commas should be ignored, common words like "not" should be kept')
    
  def testFilenameUnicode(self):
    self.assertEqual(s1('meta', u'Swedish åäö'.encode('utf-8')),
                     u'/docs/filenames/In Swedish Åäö.txt')

  def testContentXslAndOds(self):
    r = searchContent('"cell B2"')
    self.assertEqual(r['response']['numFound'], 2)
  
  def testContentDocAndOdt(self):
    r = searchContent('"Repos Search is ok"')
    self.assertEqual(r['response']['numFound'], 2)
    
  def testPDFPrintedOnOsX(self):
    self.assertEqual(s1('content', 'veryshortpdfcontents'),
                     '/docs/svnprops/shortpdf.pdf')
  
  def testContentInvalidXml(self):
    r = searchMeta('invalid not closed')
    self.assertEqual(r['response']['numFound'], 1)
    error = r['response']['docs'][0]['text_error']
    self.assertTrue(error.find('xml') >= 0, 'Got: %s' % error)
    self.assertTrue(error.find('opentag') >= 0, 'Should specify the invalid tag. Got: %s' % error)    
    self.assertEqual(r['response']['docs'][0]['svnprop_some_prop'], 'OnInvalidXml',
                     'svn properties should be indexed even if document can not be parsed')
    
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
    docs = r['response']['docs']
    self.assertEqual(len(docs), 2, 'should be two files with this keyword')    
    self.assertEqual(r['response']['docs'][1]['id'], 
                     '%s^/docs/svnprops/textwithsvnprops.txt' % reponame,
                     'meta search should include *:kewords property with likely namespaces except svn:keywords')

  def testSearchOnCustomTagsField(self):
    self.assertEqual(s1('meta', 'tagging-in-svnprop'),
                     '/docs/svnprops/textwithsvnprops.txt',
                     'meta search should include any *:tags property')
    self.assertEqual(searchMeta('tagging')['response']['numFound'], 0, 'Unlike title keywords should not be split')
    
  def testKeywordsCaseInsensitive(self):
    self.assertEqual(searchMeta('600')['response']['numFound'], 0, 'Unlike title keywords should not be split')
    self.assertEqual(s1('meta', '600K'), '/docs/svnprops/textwithsvnprops.txt')
    self.assertEqual(s1('meta', '600k'), '/docs/svnprops/textwithsvnprops.txt', 'should be case insensitive')    
    
  def testKeywordsFromPDFAndSvnProperty(self):
    r = search('allkeywords:(keywordinsaveaspdf AND keywordfromsvnprop)')
    self.assertEqual(r['response']['numFound'], 1, 'should match on both keyword from file and svn')
    doc = r['response']['docs'][0]
    self.assertEqual(doc['id'], '%s^/docs/svnprops/shortpdf.pdf' % reponame)
    self.assertEqual(doc['svnprop_svn_mime_type'], 'application/pdf', 'should index svn:mime-type')
    
  def testSearchEmbeddedPDFTitle(self):
    self.assertEqual(s1('meta', '"PDF Title"'),
                     '/docs/svnprops/shortpdf.pdf',
                     'should match on part of PDF embedded Title')

  def testTitleSvnProperty(self):
    return # is this a requirement? if so shouldn't we have an alltitles field like allkeywords
    self.assertEqual(s1('meta', 'svnproptitle addition embedded'),
                     '/docs/svnprops/shortpdf.pdf',
                     'should match *:title svn property ')
    return # fails in 1.0, the copy rule can not distinguish between namespace and property name with dash
    r = searchMeta('svnpropdoctitle')
    self.assertEqual(r['response']['numFound'], 0,
                     'default rule should only match props named "title", any namespace');    
  
  def testTitleQueryStopword(self):
    # note that stopwords are not enabled for title right now because we can't know the language
    self.assertEqual(s1('meta', 'PDF Title for Short Document'),
                     '/docs/svnprops/shortpdf.pdf',
                     'if stopwords are filtered out at indexing they should be filtered out from query too')

  def testSearchEmbeddedPDFSubject(self):
    # TODO Should subject be matched in meta query?    
    self.assertEqual(s1('standard', 'subject:"PDF subject"'),
                     '/docs/svnprops/shortpdf.pdf',
                     'should match on part of PDF embedded Subject')
    
  def testContentUTF8Txt(self):
    self.assertEqual(s1('content', u'ÅÄÖåäö'.encode('utf-8')),
                     u'/docs/filenames/In Swedish Åäö.txt')
    
  def testFilenameWithLeadingWhitespace(self):
    '''Subversion and some OSes support filenames that start with whitespace'''
    (h, f) = tempfile.mkstemp()
    # note that this name looks weird in svnlook tree
    run(['svn', 'import', "%s" % f, repourl + '/ leadingwhitespace.txt', '-m', 'OK name?'])
    os.remove(f)
    self.assertEqual(s1('meta', 'leadingwhitespace'),
                     '/ leadingwhitespace.txt',
                     'Subversion allowes names taht start with whitespace so we should too')
    
  def testFileDelete(self):
    (h, f) = tempfile.mkstemp()
    run(['svn', 'import', "%s" % f, repourl + '/tobedeleted.txt', '-m', 'Add'])
    os.remove(f)
    self.assertEqual(s1('meta', 'tobedeleted'),'/tobedeleted.txt')
    run(['svn', 'rm', repourl + '/tobedeleted.txt', '-m', 'Remove'])
    self.assertEqual(searchMeta('tobedeleted')['response']['numFound'], 0)    
    
  def testFolderDelete(self):
    d = tempfile.mkdtemp()
    df = open(d + '/fileinshortlivedfolder', 'w').close()
    run(['svn', 'import', "%s" % d, repourl + '/shortlived.folder', '-m', 'Add folder with file'])
    # check that names starting with the exact same string are not deleted
    run(['svn', 'import', "%s" % d, repourl + '/shortlived.folder2', '-m', 'Add folder with file 2'])
    rmtree(d)
    self.assertEqual(searchMeta('fileinshortlivedfolder')['response']['numFound'], 2)
    run(['svn', 'rm', repourl + '/shortlived.folder', '-m', 'Remove folder'])
    self.assertEqual(searchMeta('fileinshortlivedfolder')['response']['numFound'], 1) 
    
  def testVeryLongPropertyValue(self):
    self.assertEqual(s1('meta', 'longpropertyvalue.txt'),
                     '/docs/svnprops/longpropertyvalue.txt',
                     'longpropertyvalue.txt is not indexed, maybe the server can\'t handle 30k http headers')
    
  def testMd5(self):
    r = search('md5:64458944e1162dfcf05673d24dfdd0f6', 'standard', 'svnrev')
    self.assertEqual(r['response']['numFound'], 1)    
    self.assertEqual(r['response']['docs'][0]['id'], 
                     '%s^/docs/OpenOffice Calc.ods@1' % reponame)
    self.assertEqual(r['response']['docs'][0]['rev'], 1);
    r = search('md5:68b329da9893e34099c7d8ad5cb9c940', 'standard', 'svnrev')
    self.assertEqual(r['response']['numFound'], 5, "all test documents with only a newline")
  
  def testSha1(self):
    r = search('sha1:43b02cb0b0681f1dbe34145af744fb7b2a587eca', 'standard', 'svnrev')
    self.assertEqual(r['response']['numFound'], 1)
    self.assertEqual(r['response']['docs'][0]['id'], 
                     '%s^/docs/OpenOffice Calc.ods@1' % reponame)
    self.assertEqual(r['response']['docs'][0]['rev'], 1);    
  
  def testNonasciiPath(self):
    self.assertEqual(s1('meta', u'über'.encode('utf-8')), u'/docs/nötäscii/über.bin')
    run(['svn', 'rm', repourl + u'/docs/nötäscii', '-m', 'Delete folder not ascii'])
    r = searchMeta(u'über'.encode('utf-8'))
    self.assertEqual(r['response']['numFound'], 0, 'svnhead should now have deleted the folder contents')
  
  def testFolderFacetingInHead(self):
    schema = 'svnhead'
    query = 'q=extension:txt&indent=on&wt=json&rows=1&facet=on&facet.field=folder&fq=id_repo:%s' % reponame
    query = query + '&mincount=1'
    c = curl(solr + schema + '/select?' + query)
    r = json.loads(c)
    # Note that folders from all repositories will be in the result but count will be 0 if not matched in q and fq
    facet = r['facet_counts']['facet_fields']['folder'];
    # The json structure is, oddly, an array for facet results
    folders = dict()
    i = 0
    while (i < len(facet)):
      folders[facet[i]] = facet[i + 1]
      i = i + 2
    
    self.assertEqual(folders['/docs/filenames/'], 6)
    self.assertEqual(folders['/docs/svnprops/'], 2)
    self.assertEqual(folders['/'], 1)
    self.assertEqual(folders['/docs/'], 0)
    
  def testImageMetadata(self):
    r = search('testJPEG_commented_pspcs2mac')
    self.assertEqual(r['response']['numFound'], 1, 'should find image')
    doc = r['response']['docs'][0]
    self.assertEqual(doc['content_type'], 'image/jpeg')
    self.assertEqual(doc['title'], u'Tosteberga Ängar')
    self.assertEqual(doc['author'], u'Some Tourist')
    self.assertEqual(doc['description'], u'Bird site in north eastern Skåne, Sweden.\n(new line)')
    self.assertTrue(u"bird watching" in doc['keywords'])
    # There is no time zone info in EXIF date. This is at 09:02 in UTC but only CPS timestamp shows that.
    #self.assertEqual(doc['date'], '2010:07:28T11:02:12', 'EXIF date time created (digitized)')
    # geotags
    self.assertEqual(doc['geo_lat'], 56.0125)
    self.assertEqual(doc['geo_long'], 14.46278)
    
  def testImageComment(self):
    docs = search('description:"Bird site in north eastern"')['response']['docs']
    ids = [docs[i]['id'].partition('^')[2] for i in range(len(docs))]
    #print("comment matches: " + repr(ids))
    self.assertTrue('/docs/images/testJPEG_commented_gthumb.jpg' in ids)
    self.assertTrue('/docs/images/testJPEG_commented_xnviewmp026.jpg' in ids)
    self.assertTrue('/docs/images/testJPEG_commented_acdseemac.jpg' in ids)
    self.assertTrue('/docs/images/testJPEG_commented_acdsee9.jpg' in ids)
    self.assertTrue('/docs/images/testJPEG_commented_itag.jpg' in ids)
    self.assertTrue('/docs/images/testJPEG_commented_pspcs2mac.jpg' in ids)
    #self.assertTrue('/docs/images/testJPEG_commented_digikam120.jpg' in ids, 'comments as XMP only by default')

  def testImageCommentNonAscii(self):
    docs = search(u'description:"Bird site in north eastern Skåne"'.encode('utf-8'))['response']['docs']
    ids = [docs[i]['id'].partition('^')[2] for i in range(len(docs))]
    # only exif: self.assertTrue('/docs/images/testJPEG_commented_gthumb.jpg' in ids)
    self.assertTrue('/docs/images/testJPEG_commented_xnviewmp026.jpg' in ids)
    self.assertTrue('/docs/images/testJPEG_commented_acdseemac.jpg' in ids)
    self.assertTrue('/docs/images/testJPEG_commented_acdsee9.jpg' in ids)
    self.assertTrue('/docs/images/testJPEG_commented_itag.jpg' in ids)
    self.assertTrue('/docs/images/testJPEG_commented_pspcs2mac.jpg' in ids)
    
  def testImageTitle(self):
    #docs = search('title:"Tosteberga Ängar"')['response']['docs']
    docs = search('title:"Tosteberga"')['response']['docs']
    ids = [docs[i]['id'].partition('^')[2] for i in range(len(docs))]
    #print("title matches: " + repr(ids))
    self.assertTrue('/docs/images/testJPEG_commented_acdseemac.jpg' in ids)
    #self.assertTrue('/docs/images/testJPEG_commented_xnviewmp026.jpg' in ids, 'tagged as Iptc.Application2.Headline')
    
  def testImageAuthor(self):
    docs = search('author:"Some Tourist"')['response']['docs']
    ids = [docs[i]['id'].partition('^')[2] for i in range(len(docs))]
    #print("author matches: " + repr(ids))  
    self.assertTrue('/docs/images/testJPEG_commented_acdseemac.jpg' in ids)
    
  def testCopyFolderAndMoveFolder(self):
    (h, f) = tempfile.mkstemp()
    os.write(h, 'copytest1\n')
    os.close(h)
    url = repourl + u'/copytest'
    run(['svn', 'import', "%s" % f, url + '/folder/copytestfile.txt', '-m', 'Add'])
    os.remove(f)
    run(['svn', 'cp', url + '/folder', url + '/folder2', '-m', 'Copy folder'])
    run(['svn', 'mv', url + '/folder2', url + '/trunk', '-m', 'Move folder'])
    head = search('copytestfile')
    self.assertEqual(head['response']['numFound'], 2) # HEAD should have one original and one copy-of-copy    
    rev = search('sha1:d42b3a3e79abf906c3be39410f4aa6f64a7d1c93', 'standard', 'svnrev')
    self.assertEqual(rev['response']['numFound'], 3) # rev should have original, a copy that has later been moved and a copy-of-copy
    run(['svn', 'mkdir', url + '/branches', '-m', 'Create branches folder according to naming convention'])
    # testing with move instead of copy, the hook does not detect that so with default options it should result in -1 hit on contents
    run(['svn', 'mv', url + '/trunk', url + '/branches/1.0', '-m', 'Make a typical branch operation'])
    head = search('copytestfile')
    self.assertEqual(head['response']['numFound'], 1) # branch contents should be ignored when running hook with default options
    rev = search('sha1:d42b3a3e79abf906c3be39410f4aa6f64a7d1c93', 'standard', 'svnrev')
    self.assertEqual(rev['response']['numFound'], 3) # branch contents should be ignored when running hook with default options
 
  def testMoveFolderWithFileChange(self):
    # use a quite small folder to make the test faster, doesn't matter much which one
    (h, f) = tempfile.mkstemp()
    os.write(h, 'copytestII')
    os.close(h)
    url = repourl + u'/copytest2'    
    run(['svn', 'import', "%s" % f, url + '/folder/copytest2file.txt', '-m', 'Add'])
    os.remove(f)
    wc = tempfile.mkdtemp()
    run(['svn', 'co', url, wc])
    run(['svn', 'propset', 'copytestprop', 'copytestvalue', wc + '/folder/copytest2file.txt'])
    run(['svn', 'cp', wc + '/folder', wc + '/folder2'])
    run(['svn', 'ci', wc, '-m', 'Copy folder'])
    run(['svn', 'mv', wc + '/folder2', wc + '/folder3'])
    fd = open(wc + '/folder3/copytest2file.txt', 'a')
    fd.write('modified\n')
    fd.close()
    run(['svn', 'ci', wc, '-m', 'Move folder'])
    run(['svnlook', 'changed', repo, '/copytest2'])
    shutil.rmtree(wc)
    # search for content in HEAD, should be two copies
    self.assertEqual(s1('content', 'copytestII'), '/copytest2/folder/copytest2file.txt')
    self.assertEqual(s1('content', 'copytestIImodified'), '/copytest2/folder3/copytest2file.txt')
    self.assertEqual(search('svnprop_copytestprop:copytestvalue')['response']['numFound'], 2)
    # svnrev, should be three copies with a modification in the last one
    revs = search('id:' + reponame + '*/copytest2file.txt@*', 'standard', 'svnrev')['response']['docs']
    self.assertEqual(len(revs), 3)
    self.assertTrue(revs[0]['id'].find('/folder/copytest2file.txt@')>0, 'got:' + revs[0]['id'])
    self.assertEqual(revs[0]['sha1'], '550339a3b71669b5ada7ae06bb3e3c1efb7a5596')
    self.assertTrue(revs[1]['id'].find('/folder2/copytest2file.txt@')>0, 'got:' + revs[1]['id'])
    self.assertEqual(revs[1]['sha1'], '550339a3b71669b5ada7ae06bb3e3c1efb7a5596')
    self.assertTrue(revs[2]['id'].find('/folder3/copytest2file.txt@')>0, 'got:' + revs[2]['id'])
    self.assertEqual(revs[2]['sha1'], 'b3e21636a85c562337c460cb541fb14a4bc134d3') # file changed inside the move

if __name__ == '__main__':
  createRepository()
  createInitialStructure()
  unittest.main()
  rmtree(repo)
  
