#!/usr/bin/python

import git_workflow_quality

import os

os.chdir('tests/test1.git')
repo = git_workflow_quality.repository()

for sha in repo.order :
    c = repo.commits[sha]
    if c.forks and not c.child :
        print "ERROR - %s" % c

git_workflow_quality.gitgraphjs.graph( repo , 'date' )

