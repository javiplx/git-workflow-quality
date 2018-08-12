#!/usr/bin/python

import git_workflow_quality

import os

os.chdir('tests/test1.git')
repo = git_workflow_quality.Repository()

sha = 'b8285f2f001cfad3eacfb5c642623822f5fb60a1'
if sha in repo :
    print "OK - Initial commit included"
else :
    print "ERROR - commit %s discarded" % sha

sha = 'b8285f2f001cfad3eacfb5c642623822f5fb60a1'
c = repo.get(sha)
if c and c.branch.name == 'master' :
    print "OK - %s" % c
else :
    print "ERROR - %s" % c

sha = '3dec0a264f6b28901cf2151e70d5691b696a4e9d'
c = repo.get(sha)
if not c or ( c.forks and not c.child  ):
    print "ERROR - %s" % c
else :
    print "OK - %s" % c

