#!/bin/bash

function runrepo {
  NAME=$1
  FROM=$2
  if [ ! -e $NAME ]; then
    echo "Creating local sync $NAME form $FROM"
    svnadmin create $NAME
    echo -e "#!/bin/sh\nexit 0" > $NAME/hooks/pre-revprop-change
    chmod u+x $NAME/hooks/pre-revprop-change
    svnsync init file://$(pwd)/$NAME $FROM
  else
    echo "$NAME already local, at rev $(svnlook youngest $NAME)"
  fi
  echo "Syncing $NAME"
  svnsync sync file://$(pwd)/$NAME
  # rebuild all indexes completely to make this a real test of current code
  echo "Reindexing"
  ../../hook/svnhook.py -p $(pwd)/$NAME -r "*"
}

# our home
runrepo repossearch https://labs.repos.se/svn/search/
# some images, branches
runrepo svg-edit http://svg-edit.googlecode.com/svn/

