#!/usr/bin/python

import git_workflow_quality

import os

os.chdir('tests/test1.git')
repo = git_workflow_quality.repository()

c = repo.commits['3dec0a264f6b28901cf2151e70d5691b696a4e9d']
if c.forks and not c.child :
    print "ERROR - %s" % c
else :
    print "OK - %s" % c

git_workflow_quality.gitgraphjs.graph( repo , 'date' )

