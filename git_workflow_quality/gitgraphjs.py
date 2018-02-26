
import sys

shown_branches = []

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


def graph ( repo , mode='topo' , filename='commits.js' ) :

    if not mode in ( 'topo' , 'date' ) :
        print "ERROR : unknown graph type '%s'" % mode
        return

    fd = open( filename , 'w' )

    fd.write( gitgraph_head )

    origins = [ c for c in repo.commits.values() if not c.parent ]

    for origin in origins :
        # FIXME: multiple origins could be owned by the same branch ?
        shown_branches.append( origin.branch )
        fd.write( 'var %s = gitgraph.branch({%s});\n' % ( js_varname(origin.branch) , js_branch(origin.branch) ) )

    if mode == 'date' :
        chrono_plot(repo, fd)
    elif mode == 'topo' :
        while origins :
            commit = origins.pop(0)
            forward_plot(repo, commit, origins, fd)

    fd.close()


def forward_plot ( repo , c , pending , fd=sys.stdout ) :
    first = True
    fd.write( '%s.checkout();\n' % js_varname(c.branch) )
    current_branch = c.branch
    while c.child :
        if c.parents :
            sha = c.parents[0]
            if c.forks :
                first = True
                for sha in c.forks :
                    for p in pending :
                        if p.sha in c.parents :
                            fd.write( '%s.checkout();\n' % js_varname(p.branch) )
                            fd.write( 'gitgraph.commit({sha1:"%s", message:"%s"});\n' % ( p.sha , p.message ) )
                            fd.write( '%s.checkout();\n' % js_varname(c.branch) )
                            pending.remove(p)
                            if p.child :
                                pending.append(repo.commits[p.child])
                            pending.remove( c )
                fd.write( '%s.merge(%s, {sha1:"%s", message:"%s"});\n' % ( js_varname(repo.commits[sha].branch) , js_varname(c.branch) , c.sha , c.message ) )
                if c in pending :
                    pending.remove( c )
            else :
              if repo.commits[sha].branch not in shown_branches :
                  fd.write( '%s.merge(%s, {sha1:"%s", message:"%s"});\n' % ( js_varname(repo.commits[sha].branch) , js_varname(c.branch) , c.sha , c.message ) )
              else :
                if c not in pending :
                    pending.append( c )
                break
        else :
            if first :
                first = False
                fd.write( 'gitgraph.commit({sha1:"%s", message:"%s"});\n' % ( c.sha , c.message ) )
            elif c.forks :
                first = True
                fd.write( 'gitgraph.commit({sha1:"%s", message:"%s"});\n' % ( c.sha , c.message ) )
            elif c.child and repo.commits[c.child].parents :
                fd.write( 'gitgraph.commit({sha1:"%s", message:"%s"});\n' % ( c.sha , c.message ) )
        new_branches = False
        for sha in c.forks :
            if not repo.commits[sha].parents :
                new_branches = True
                fd.write( 'var %s = gitgraph.branch({%s});\n' % ( js_varname(repo.commits[sha].branch) , js_branch( repo.commits[sha].branch , len(shown_branches) ) ) )
                shown_branches.append( repo.commits[sha].branch )
                if repo.commits[sha] not in pending :
                    pending.append( repo.commits[sha] )
            else :
              target = repo.commits[sha]
              if target not in pending :
                    for p in pending :
                        if p.sha == target.parent :
                            break
              else :
                fd.write( '%s.merge(%s, {sha1:"%s", message:"%s"});\n' % ( js_varname(c.branch) , js_varname(target.branch) , sha , target.message ) )
                fd.write( '%s.checkout();\n' % js_varname(c.branch) )
                pending.remove( target )
                pending.append( repo.commits[target.child] )
        if new_branches :
            first = True
            fd.write( '%s.checkout();\n' % js_varname(c.branch) )
        c = repo.commits[c.child]
    else :
        shown_branches.remove( current_branch )
        if c.parents :
            sha = c.parents[0]
            fd.write( '%s.merge(%s, {sha1:"%s", message:"%s"});\n' % ( js_varname(repo.commits[sha].branch) , js_varname(c.branch) , c.sha , c.message ) )
            if c in pending :
                pending.remove( c )
        else :
            fd.write( 'gitgraph.commit({sha1:"%s", message:"%s"});\n' % ( c.sha , c.message ) )
        for sha in c.forks :
            if repo.commits[sha] not in pending :
                pending.append( repo.commits[sha] )

def chrono_plot ( repo , fd=sys.stdout) :
    """Assumes that commits are properly ordered, so just the commit list is given"""
    current_branch = None
    first = True
    for sha in repo.order :
        c = repo.commits[sha]
        if not c.branch in shown_branches :
            shown_branches.append( c.branch )
            if c.parent and repo.commits[c.parent].branch != current_branch :
                fd.write( '%s.checkout();\n' % js_varname(repo.commits[c.parent].branch) )
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
            elif c.child and repo.commits[c.child].parents :
                fd.write( 'gitgraph.commit({sha1: "%s", message: "%s"});\n' % ( c.sha , c.message ) )
        else :
            fd.write( '%s.merge(%s, {sha1:"%s", message:"%s"});\n' % ( js_varname(repo.commits[c.parents[0]].branch) , js_varname(c.branch) , c.sha , c.message ) )
            if not repo.commits[c.parents[0]].child :
                if repo.commits[c.parents[0]].branch in shown_branches :
                    shown_branches.remove( repo.commits[c.parents[0]].branch )

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
