
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
<!DOCTYPE html>
<html>
<body>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gitgraph.js/1.11.4/gitgraph.min.js"></script>
<canvas id="gitGraph"></canvas>
<script type="text/javascript">
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

gitgraph_tail = """
</script>
</body>
</html>
"""


def graph ( repo , mode='topo' , filename='commits.html' ) :

    if not mode in ( 'topo' , 'date' ) :
        print "ERROR : unknown graph type '%s'" % mode
        return

    fd = open( filename , 'w' )

    fd.write( gitgraph_head )

    origins = [ c for c in repo.values() if not c.parent ]

    for origin in origins :
        # FIXME: multiple origins could be owned by the same branch ?
        shown_branches.append( origin.branch )
        origin.branch.render( fd )

    if mode == 'date' :
        chrono_plot(repo, fd)
    elif mode == 'topo' :
        while origins :
            commit = origins.pop(0)
            forward_plot(repo, commit, origins, fd)

    fd.write( gitgraph_tail )
    fd.close()


def forward_plot ( repo , c , pending , fd=sys.stdout ) :
    realFirst = True
    first = True
    current_branch = c.branch
    while c.child :
        end_of_branch = c.child.branch != current_branch
        if c.parents :
            if current_branch != c.branch :
                c.render( fd )
                pending.remove(c)
                target = c.child
                pending.append( target )
                for target in c.forks :
                    pending.append( target )
                break
            elif c.forks :
                first = True
                for child in c.forks :
                    for p in pending :
                        if p in c.parents :
                            fd.write( '%s.commit({sha1:"%s", message:"%s"});\n' % ( current_branch.as_var() , p.sha , p.message ) )
                            pending.remove(p)
                            if p.child :
                                pending.append(p.child)
                c.render( fd )
            else :
              if c.parents[0].branch not in shown_branches :
                if realFirst :
                  c.render( fd )
                else :
                  pending.append(c)
                  break
              else :
               if c not in pending :
                pending.append(c)
                if c.child :
                    if c.child.branch != current_branch :
                        pending.append( c.child )
                for child in c.forks :
                    if child.branch != current_branch :
                        pending.append( child )
               elif realFirst :
                   pending.append( c)
               break
        else :
            if first :
                first = False
                c.render(fd)
            elif c.forks :
                first = True
                c.render(fd)
            elif c.child and c.child.parents :
                c.render(fd)
            elif end_of_branch :
                c.render(fd)
        break_it = False
        for target in c.forks :
          if target.branch :
            if target.branch == current_branch :
                end_of_branch = False
            if not target.parents :
                first = True
                target.branch.render( fd , current_branch , shown_branches )
                shown_branches.append( target.branch )
                pending.append( target )
            else :
              if target not in pending :
                  # We just assume that target will appear on pending in the future
                  break_it = True
              else :
                target.render( fd , c , False )
                pending.remove( target )
                if target.child :
                    pending.append( target.child )
                for child in target.forks :
                    pending.append( child )
        if end_of_branch :
            shown_branches.remove( current_branch )
            if c.child :
                target = c.child
                if target.branch not in shown_branches :
                    target.branch.render(  fd , current_branch , shown_branches )
                    shown_branches.append( target.branch )
                    pending.append( target )
            break
        if break_it :
            if c.child :
                pending.append( c.child )
            break
        c = c.child
        realFirst = False
        if c.parents :
            for parent in c.parents :
                if parent in pending :
                    pending.append(c)
                    break_it = True
            if break_it :
                break
        # This is likey caused by some bug on branch to commit assignment
        if c.branch != current_branch and not c.parents :
            pending.append(c)
            break
    else :
        shown_branches.remove( current_branch )
        if c.parents :
            c.render( fd )
        else :
            c.render(fd)
        for child in c.forks :
            if child.branch not in shown_branches :
                child.branch.render( fd , current_branch , shown_branches )
                shown_branches.append( child.branch )
            pending.append( child )

def chrono_plot ( repo , fd=sys.stdout) :
    """Assumes that commits are properly ordered, so just the commit list is given"""
    first = True
    for c in repo.order :
      if c.branch :
        if not c.branch in shown_branches :
            first = True
            shown_branches.append( c.branch )
            c.branch.render( fd , c.parent.branch , shown_branches )
        if not c.parents :
            if first or c.forks or not c.child :
                first = False
                c.render(fd)
            elif c.child and c.child.parents :
                first = True
                c.render(fd)
        else :
            first = True
            c.render(fd)
            if not c.parents[0].child :
                if c.parents[0].branch in shown_branches :
                    shown_branches.remove( c.parents[0].branch )
        if c.child and c.branch != c.child.branch :
            shown_branches.remove(c.branch)


