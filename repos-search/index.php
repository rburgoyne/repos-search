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

function param($name, $default='') {
	return isset($_GET[$name]) ? $_GET[$name] : $default;
}

// settings for accessing solr
$solrhost = 'localhost';
$solrport = 8080;
$solrapp = '/solr/';
$schema = 'svnhead/';
// parameters for solr search
$wt = 'json';
$start = param('start', '0');
$rows = param('rows', '10');
$indent = 'on';
$qt = param('qt', 'standard');
$q = param('q');

// allow customization from local file
$custfile = dirname(__FILE__).'/proxysettings.php';
if (file_exists($custfile)) {
	require($custfile);
}

// forward to search page if there is no query
if (!$q) {
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
$query = 'q='.rawurlencode($q);
$fq = '';
if (param('base')) {
	$fq .= '&fq=id_repo:'.rawurlencode(param('base')); // may be space separated
}
// search URI
$url = "http://$solrhost:$solrport$solrapp$schema".'select/';
// request parameters
$url .= "?$query$fq&qt=$qt&wt=$wt&start=$start&rows=$rows&indent=$indent";

$fp = @fopen($url, 'r');
if ($fp) {
	fpassthru($fp);
	fclose($fp);
} else {
	header('HTTP/1.1 503 Service Unavailable');
	echo "Search engine error. Not available or query is invalid.\n";
}

?>
