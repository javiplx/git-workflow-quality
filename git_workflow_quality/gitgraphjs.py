
import sys

gitgraph_head = """
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

"""

def open ( filename='commits.js' ) :
    fd = open( filename , 'w' )
    fd.write( gitgraph_head )
    return fd


shown_branches = []

def forward_plot ( c , pending , fd=sys.stdout ) :
    first = True
    fd.write( '%s.checkout();\n' % js_varname(c.branch) )
    while c.child :
        if c.parents :
            sha = c.parents[0]
            if commits[sha].branch in shown_branches :
                first = True
                fd.write( '%s.merge(%s, {sha1:"%s", message:"%s"});\n' % ( js_varname(commits[sha].branch) , js_varname(c.branch) , c.sha , c.message ) )
            else :
                break
        else :
            if first :
                first = False
                fd.write( 'gitgraph.commit({sha1:"%s", message:"%s"});\n' % ( c.sha , c.message ) )
            elif c.forks :
                first = True
                fd.write( 'gitgraph.commit({sha1:"%s", message:"%s"});\n' % ( c.sha , c.message ) )
        new_branches = False
        for sha in c.forks :
            first = True
            if not commits[sha].branch in shown_branches :
                new_branches = True
                fd.write( 'var %s = gitgraph.branch({%s});\n' % ( js_varname(commits[sha].branch) , js_branch( commits[sha].branch , len(shown_branches) ) ) )
                shown_branches.append( commits[sha].branch )
            if commits[sha] not in pending :
                pending.append( commits[sha] )
        if new_branches :
            first = True
            fd.write( '%s.checkout();\n' % js_varname(c.branch) )
        c = commits[c.child]
    else :
        if c.parents :
            sha = c.parents[0]
            if commits[sha].branch in shown_branches :
                fd.write( '%s.merge(%s, {sha1:"%s", message:"%s"});\n' % ( js_varname(commits[sha].branch) , js_varname(c.branch) , c.sha , c.message ) )
        else :
            fd.write( 'gitgraph.commit({sha1:"%s", message:"%s"});\n' % ( c.sha , c.message ) )
        for sha in c.forks :
            if commits[sha] not in pending :
                pending.append( commits[sha] )

def chrono_plot ( sha_list , fd=sys.stdout) :
    """Assumes that commits are properly ordered, so just the commit list is given"""
    current_branch = None
    first = True
    for sha in sha_list :
        c = commits[sha]
        if not c.branch in shown_branches :
            shown_branches.append( c.branch )
            if c.parent and commits[c.parent].branch != current_branch :
                fd.write( '%s.checkout();\n' % js_varname(commits[c.parent].branch) )
            fd.write( 'var %s = gitgraph.branch({%s});\n' % ( js_varname(c.branch) , js_branch( c.branch , len(shown_branches) ) ) )
            first = True
        elif current_branch != c.branch :
            fd.write( '%s.checkout();\n' % js_varname(c.branch) )
            first = True
        current_branch = c.branch
        if not c.parents :
            if first or c.forks :
                first = False
                fd.write( 'gitgraph.commit({sha1: "%s", message: "%s"});\n' % ( c.sha , c.message ) )
        else :
            fd.write( '%s.merge(%s, {sha1:"%s", message:"%s"});\n' % ( js_varname(commits[c.parents[0]].branch) , js_varname(c.branch) , c.sha , c.message ) )
            if not commits[c.parents[0]].child :
                if commits[c.parents[0]].branch in shown_branches :
                    shown_branches.remove( commits[c.parents[0]].branch )

def js_varname ( var ) :
    return "branch_" + var.replace(' (?)','').replace('/', '_slash_' ).replace('-', '_dash_').replace('.', '_dot_').replace(' ', '_white_').replace(':', '_colon_')

def js_branch ( name , count=2 ) :
    json = 'name:"%s"' % name
    if name == 'master' :
        json += ", column:0"
    elif name == 'develop' :
        json += ", column:1"
    else :
        json += ", column:%d" % count
    return json

