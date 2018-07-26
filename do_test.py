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

os.chdir('../..')


def test_event ( event ) :
    os.chdir( 'tests/%s.git' % event )
    repo = git_workflow_quality.Repository()
    count = repo.event_list()[0][event]
    if count == 1 :
        print "OK - 1 %s found" % event
    else :
        print "ERROR - %d %s found" % ( count , event )
    os.chdir('../..')

test_event( 'multitarget' )
test_event( 'reutilized' )
test_event( 'multimerged' )
test_event( 'indirect' )
test_event( 'multisource' )
test_event( 'conflict' )

