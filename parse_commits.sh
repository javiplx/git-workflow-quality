#!/bin/bash

[ -f branches.list ] || find .git/refs/remotes/origin -type f | while read file ; do
  echo $( cat $file ) ${file#.git/refs/remotes/origin/}
  done > branches.list

cat commits.list | sort -n -k3,3 -k 2,2 | ./parse_commits.py

