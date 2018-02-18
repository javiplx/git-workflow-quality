#!/bin/bash

if [ ! -d "$1" ] ; then
  echo No $1 test repository
  exit 1
  fi

cd $1

git log --all --format="%H %at %ct %P" > commits.list
git log --all --format="%H %ae %ce %s" > messages.list

[ -f branches.list ] || find .git/refs/heads -type f | while read file ; do
  echo $( cat $file ) ${file#.git/refs/heads/}
  done > branches.list

cat commits.list | sort -n -k3,3 -k 2,2 | python ../../parse_commits.py

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

