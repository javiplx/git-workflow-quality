#!/usr/bin/python

import git_workflow_quality

import os

os.chdir('tests/test1.git')
repo = git_workflow_quality.Repository()

c = repo['b8285f2f001cfad3eacfb5c642623822f5fb60a1']
if c.branch.name == 'master' :
    print "OK - %s owned by master" % c.sha
else :
    print "ERROR - %s owned by %s" % ( c.sha , c.branch.name )

c = repo['3dec0a264f6b28901cf2151e70d5691b696a4e9d']
if c.forks and not c.child :
    print "ERROR - %s got no child assigned" % c.sha
else :
    print "OK - child assigned to %s" % c.sha

git_workflow_quality.gitgraphjs.graph( repo , 'date' )

