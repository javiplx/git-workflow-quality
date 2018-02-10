#!/bin/bash

git log --all --format="%H %at %ct %P" > commits.list
git log --all --format="%H %ae %ce %s" > messages.list
 
tar -czf gitgraph.tar.gz .git/refs commits.list messages.list

