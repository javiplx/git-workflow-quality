#!/usr/bin/env python

import git_workflow_quality

import sys


commits , order = git_workflow_quality.get_commits()


fd = open( "commits.js" , 'w' )

fd.write( """
var myTemplateConfig = {
  colors: [ "#9993FF", "#47E8D4", "#6BDB52", "#F85BB5", "#FFA657", "#F85BB5" ],
  branch: {
    lineWidth: 2,
    spacingX: 40,
    showLabel: true, // display branch names on graph
    labelFont: "normal 10pt Arial",
    labelRotation: 0
  },
  commit: {
    spacingY: -30,
    dot: {
      size: 6,
      lineDash: [2]
    },
    message: {
      font: "normal 12pt Arial"
    },
    tooltipHTMLFormatter: function (commit) {
      return "<b>" + commit.sha1 + "</b>" + ": " + commit.message;
    }
  },
  arrow: {
    size: 6,
    offset: 1
  }
};

var myTemplate = new GitGraph.Template(myTemplateConfig);

var config = {
  template: myTemplate, // "blackarrow",
  reverseArrow: false,
  orientation: "horizontal",
  mode: "compact"
};

var gitgraph = new GitGraph(config);

""" )


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

