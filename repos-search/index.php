<?php 
/** Search proxy

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

Trivial proxy for Solr queries: has access to the webapp, 
adds query defaults, filters on base if available. 
$LastChangedRevision$
 */

// settings for accessing solr
$solrhost = 'localhost';
$solrport = 8080;
$solrapp = '/solr/';
$schema = 'svnhead/';
// parameters for solr search
$wt = 'json';
$start = 0;
$rows = 10;
$indent = 'on';

// forward to search page if there is no query
if (!isset($_GET['q'])) {
?>
<html>
<head>
<title>Repos Search proxy: no query yet</title>
<meta http-equiv="refresh" content="1;url=search.html" />
</head>
<body>
<p>Redirecting to <a href="search.html">sample search form</a> becase <code>q</code> is not set.</p>
</body>
</html>
<?php
exit;
}

header('Content-Type: text/plain');
// the search
$query = 'q='.rawurlencode($_GET['q']);
$fq = '';
if (isset($_GET['base'])) {
	$fq .= '&fq=id_repo:'.$_GET['base']; // may not contain non-URI characters
}
// search URI
$url = "http://$solrhost:$solrport$solrapp$schema".'select/';
// request parameters
$url .= "?$query$fq&wt=$wt&start=$start&rows=$rows&indent=$indent";

$fp = fopen($url, 'r');
fpassthru($fp);
fclose($fp);

?>
