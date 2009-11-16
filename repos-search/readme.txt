Repos Search (c) Staffan Olsson reposstyle.com


For help use the mailing list found at http://reposstyle.com/


Installation of Repos Search indexing hook
------------------------------------------

First of all the indexing server must be running. See project documentation.

Call svnhook.py in this folder from the post-commit hook in your repository/ies.
It is useful for troubleshooting to redirect stdout and stderr to a log file.
Also as this hook reads the committed data from repository it is important to
run indexing as a background process (append &).
Example for post-commit bash script:
# full text search
/usr/bin/python /myhost/repos-search/hook/svnhook.py -p $1 -r $2 >> /mylogs/hooks.log 2>&1 &
# for options type: python svnhook.py --help
