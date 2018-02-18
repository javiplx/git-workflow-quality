#!/usr/bin/env python

import git_workflow_quality

import sys


commits , order = git_workflow_quality.get_commits()

fd = git_workflow_quality.gitgraphjs.open()

origins = []
for c in commits.values() :
    if not c.parent :
        origins.append( c )

for origin in origins :
    # FIXME: multiple origins could be owned by the same branch ?
    shown_branches.append( origins[0].branch )
    fd.write( 'var %s = gitgraph.branch({%s});\n' % ( js_varname(origins[0].branch) , js_branch(origins[0].branch) ) )

if len(sys.argv) > 1 and sys.argv[1] == 'date' :
    order.reverse()
    chrono_plot(order, fd)
else :
    while origins :
        commit = origins.pop(0)
        forward_plot(commit, origins, fd)

fd.close()

