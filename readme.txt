Repos Search (c) Staffan Olsson reposstyle.com


Installation
------------

1.
Build and start Solr 1.4-dev example application using the instructions at
http://wiki.apache.org/solr/ExtractingRequestHandler

2.
After "example" jetty is started Solr should be found at http://localhost:8983/solr/

3.
Call hook.py in this folder from the post-commit hook in your repository/ies.
It is useful for troubleshooting to redirect stdout and stderr to a log file.
Also as this hook reads the committed data from repository it is important to
run indexing as a background process (append &).
Example for post-commit bash script:
# full text search
/usr/bin/python /myhost/repos-search/hook.py -p $1 -r $2 >> /mylogs/hooks.log 2>&1 &
# for options type: python hook.py --help

4.
Add jQuery and repos-search.load.js to Repos Style <head> (in view/repos.xsl)
<!-- Repos Search -->
<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js"></script>
<script type="text/javascript" src="/repos-search/repos-search.load.js"></script>
