#!/bin/bash

if [ ! -d "$1" ] ; then
  echo No $1 test repository
  exit 1
  fi

cd $1

python ../../git-workflow-quality date

cat <<HTML > index.html
<!DOCTYPE html>
<html>
<body>
<canvas id="gitGraph"></canvas>
<script src="gitgraph.js"></script>
<script src="commits.js"></script>
</body>
</html>
HTML

test -f gitgraph.js || curl -s -O https://raw.githubusercontent.com/nicoespeon/gitgraph.js/master/src/gitgraph.js

