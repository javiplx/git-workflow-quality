
import sys


class nullable_list ( list ) :

    def append ( self , item ) :
        if None in self :
            idx = self.index(None)
            self[idx] = item
        else :
            list.append( self , item )

    def remove ( self , item ) :
        idx = self.index(item)
        self[idx] = None

shown_branches = nullable_list()


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


class unique_list ( list ) :

    def append ( self , item ) :
        if item not in self :
            list.append( self , item )

    def remove ( self , item ) :
        if item in self :
            list.remove( self , item )


def graph ( repo , mode='topo' , filename='commits.js' ) :

    if not mode in ( 'topo' , 'date' ) :
        print "ERROR : unknown graph type '%s'" % mode
        return

    fd = open( filename , 'w' )

    fd.write( gitgraph_head )

    origins = unique_list([ c for c in repo.commits.values() if not c.parent ])

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
    current_branch = c.branch
    while c.child :
        if c.parents :
            sha = c.parents[0]
            if current_branch == repo.commits[sha].branch :
                c.render( fd , repo.commits[sha] )
                pending.remove(c)
                for sha in c.forks :
                    target = repo.commits[sha]
                    fd.write( 'var %s = %s.branch({%s});\n' % ( js_varname(target.branch) , js_varname(current_branch) , js_branch( target.branch , len(shown_branches) ) ) )
                    shown_branches.append( target.branch )
                    pending.append( target )
                break
            elif c.forks :
                first = True
                for sha in c.forks :
                    for p in pending :
                        if p.sha in c.parents :
                            fd.write( '%s.commit({sha1:"%s", message:"%s"});\n' % ( js_varname(current_branch) , p.sha , p.message ) )
                            pending.remove(p)
                            if p.child :
                                pending.append(repo.commits[p.child])
                c.render( fd , repo.commits[sha] )
                pending.remove( c )
            else :
              if repo.commits[sha].branch not in shown_branches :
                  c.render( fd , repo.commits[sha] )
                  shown_branches.remove( current_branch )
                  pending.remove(c)
              else :
                pending.append(c)
                if c.child :
                    pending.append( repo.commits[c.child] )
                for sha in c.forks :
                    pending.append( repo.commits[sha] )
                break
        else :
            if first :
                first = False
                c.render(fd)
            elif c.forks :
                first = True
                c.render(fd)
            elif c.child and repo.commits[c.child].parents :
                c.render(fd)
            pending.remove(c)
        for sha in c.forks :
            if not repo.commits[sha].parents :
                first = True
                fd.write( 'var %s = %s.branch({%s});\n' % ( js_varname(repo.commits[sha].branch) , js_varname(current_branch) , js_branch( repo.commits[sha].branch , len(shown_branches) ) ) )
                shown_branches.append( repo.commits[sha].branch )
                pending.append( repo.commits[sha] )
            else :
              target = repo.commits[sha]
              if target not in pending :
                    for p in pending :
                        if p.sha == target.parent :
                            break
              else :
                target.render( fd , c )
                pending.remove( target )
                if target.child :
                    pending.append( repo.commits[target.child] )
        c = repo.commits[c.child]
        # This is likey caused by some bug on branch to commit assignment
        if c.branch != current_branch and not c.parents :
            pending.append(c)
            break
    else :
        shown_branches.remove( current_branch )
        if c.parents :
            sha = c.parents[0]
            c.render( fd , repo.commits[sha] )
            pending.remove( c )
        else :
            c.render(fd)
        for sha in c.forks :
            if repo.commits[sha].branch not in shown_branches :
                shown_branches.append( repo.commits[sha].branch )
            pending.append( repo.commits[sha] )

def chrono_plot ( repo , fd=sys.stdout) :
    """Assumes that commits are properly ordered, so just the commit list is given"""
    first = True
    for sha in repo.order :
        c = repo.commits[sha]
        if not c.branch in shown_branches :
            first = True
            shown_branches.append( c.branch )
            fd.write( 'var %s = %s.branch({%s});\n' % ( js_varname(c.branch) , js_varname(repo.commits[c.parent].branch) , js_branch( c.branch , len(shown_branches) ) ) )
        if not c.parents :
            if first or c.forks or not c.child :
                first = False
                c.render(fd)
            elif c.child and repo.commits[c.child].parents :
                first = True
                c.render(fd)
        else :
            first = True
            c.render(fd, repo.commits[c.parents[0]])
            if not repo.commits[c.parents[0]].child :
                if repo.commits[c.parents[0]].branch in shown_branches :
                    shown_branches.remove( repo.commits[c.parents[0]].branch )
        if c.child and c.branch != repo.commits[c.child].branch :
            shown_branches.remove(c.branch)


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

