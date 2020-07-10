#!/usr/bin/env python2

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

sha = 'b8285f2f001cfad3eacfb5c642623822f5fb60a1'
if sha in repo :
    ret += ok( "Initial commit included" )
else :
    ret += fail( "commit %s discarded" % sha )

sha = 'b8285f2f001cfad3eacfb5c642623822f5fb60a1'
c = repo.get(sha)
if c and c.branch.name == 'master' :
    ret += ok( "%s owned by master" % sha )
else :
    ret += fail( "%s not on master branch" % sha )

sha = '3dec0a264f6b28901cf2151e70d5691b696a4e9d'
c = repo.get(sha)
if not c or ( c.forks and not c.child  ):
    ret += fail( "%s got no child assigned" % sha )
else :
    ret += ok( "child assigned to %s" % sha )

os.chdir('../..')


os.chdir( 'tests/multitarget.git' )
repo = git_workflow_quality.Repository()
count = len(repo.branches)
if count == 4 :
    ret += ok( "branch concatenation working" )
else :
    ret += fail( "branch concatenation produced %d branches" % count )
os.chdir('../..')


os.chdir( 'tests/multitarget.git' )
repo = git_workflow_quality.Repository()
count = len(repo.branches)
if count == 4 :
    ret += ok( "branch concatenation working" )
else :
    ret += fail( "branch concatenation produced %d branches" % count )
os.chdir('../..')


os.chdir( 'tests/branchcount.git' )
repo = git_workflow_quality.Repository()
count = len(repo.branches)
if count == 5 :
    ret += ok( "branch count working" )
else :
    ret += fail( "counted %d branches" % count )
os.chdir('../..')


os.chdir( 'tests/complexnetwork.git' )
repo = git_workflow_quality.Repository()
count = len([ c for c in repo.values() if not c.child ])
if count == 2 :
    ret += ok( "open branches properly found" )
else :
    ret += fail( "found %d opened branches" % count )
#
count = repo.event_list()[0]['multimerged']
if count == 1 :
    ret += ok( "1 multimerged found" )
else :
    ret += fail( "%d multimerged found" % count )
#
count = repo.event_list()[0]['conflict']
if count == 1 :
    ret += ok( "1 conflict found" )
else :
    ret += fail( "%d conflict found" % count )
#
count = len(repo.branches)
if count == 8 :
    ret += ok( "complex branches properly concatenated" )
else :
    ret += fail( "complex concatenation produced %d branches" % count )
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

