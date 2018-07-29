#!/usr/bin/env python

import git_workflow_quality

import os

def ok( msg , fd=os.sys.stdout ) :
    if os.environ['TERM'] == 'cygwin':
        fd.write( "OK - %s\n" % msg )
    else :
        fd.write( "\033[1;32mOK\033[1;m - %s\n" % msg )
    return 0

def fail( msg , fd=os.sys.stdout ) :
    if os.environ['TERM'] == 'cygwin':
        fd.write( "ERROR - %s\n" % msg )
    else :
        fd.write( "\033[1;31mERROR\033[1;m - %s\n" % msg )
    return 1

ret = 0

os.chdir('tests/test1.git')
repo = git_workflow_quality.Repository()

c = repo['b8285f2f001cfad3eacfb5c642623822f5fb60a1']
if c.branch.name == 'master' :
    ok( "%s owned by master" % c.sha )
else :
    ret += fail( "%s on branch" % ( c.sha , c.branch.name ) )

c = repo['3dec0a264f6b28901cf2151e70d5691b696a4e9d']
if c.forks and not c.child :
    ret += fail( "%s got no child assigned" % c.sha )
else :
    ret += ok( "child assigned to %s" % c.sha )

os.chdir('../..')


os.chdir( 'tests/multitarget.git' )
repo = git_workflow_quality.Repository()
count = len(repo.branches)
if count == 4 :
    ret += ok( "branch concatenation working" )
else :
    ret += fail( "branch concatenation produced %d branches" % count )
os.chdir('../..')


def test_event ( event ) :
    os.chdir( 'tests/%s.git' % event )
    repo = git_workflow_quality.Repository()
    count = repo.event_list()[0][event]
    if count == 1 :
        ret = ok( "1 %s found" % event )
    else :
        ret = fail( "%d %s found" % ( count , event ) )
    os.chdir('../..')
    return ret

ret += test_event( 'multitarget' )
ret += test_event( 'reutilized' )
ret += test_event( 'multimerged' )
ret += test_event( 'indirect' )
ret += test_event( 'multisource' )
ret += test_event( 'conflict' )

os.sys.exit(ret)

