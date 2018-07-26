#!/usr/bin/env python

import git_workflow_quality

import os

ret = 0

os.chdir('tests/test1.git')
repo = git_workflow_quality.Repository()

c = repo['b8285f2f001cfad3eacfb5c642623822f5fb60a1']
if c.branch.name == 'master' :
    print "\033[1;32mOK\033[1;m - %s owned by master" % c.sha
else :
    print "\033[1;31mERROR\033[1;m - %s" % ( c.sha , c.branch.name )
    ret += 1

c = repo['3dec0a264f6b28901cf2151e70d5691b696a4e9d']
if c.forks and not c.child :
    print "\033[1;31mERROR\033[1;m - %s got no child assigned" % c.sha
    ret += 1
else :
    print "\033[1;32mOK\033[1;m - child assigned to %s" % c.sha

os.chdir('../..')


def test_event ( event ) :
    os.chdir( 'tests/%s.git' % event )
    repo = git_workflow_quality.Repository()
    count = repo.event_list()[0][event]
    if count == 1 :
        print "\033[1;32mOK\033[1;m - 1 %s found" % event
	ret = 0
    else :
        print "\033[1;31mERROR\033[1;m - %d %s found" % ( count , event )
	ret = 1
    os.chdir('../..')
    return ret

ret += test_event( 'multitarget' )
ret += test_event( 'reutilized' )
ret += test_event( 'multimerged' )
ret += test_event( 'indirect' )
ret += test_event( 'multisource' )
ret += test_event( 'conflict' )

os.sys.exit(ret)

