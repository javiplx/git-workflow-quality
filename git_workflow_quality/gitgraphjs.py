
import sys


class nullable_list ( list ) :

    reserved = 0

    def append ( self , item , fd , parent=None ) :
        if None in self[self.reserved:] :
            idx = self.reserved + self[self.reserved:].index(None)
            self[idx] = item
        else :
            list.append( self , item )
        item.render( fd , parent , self )

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
        shown_branches.append( origin.branch , fd )
    shown_branches.reserved = len([b for b in repo.branches.values() if b.is_primary()])

    if mode == 'date' :
        chrono_plot(repo, fd)
    elif mode == 'topo' :
        while origins :
            commit = origins.pop(0)
            forward_plot(repo, commit, origins, fd)

    fd.write( gitgraph_tail )
    fd.close()


def forward_plot ( repo , c , pending , fd=sys.stdout ) :
    first = True
    current_branch = c.branch
    while c.child :
        end_of_branch = len([ C for C in c.get_childs() if C.branch == current_branch ]) == 0
        if c.parents :
            if [ p for p in c.get_parents() if not p.rendered ] :
                pending.append(c)
                break
            else :
                c.render( fd , c.parents[0] )
        else :
            if first :
                first = False
                c.render(fd)
            elif c.forks :
                c.render(fd)
            elif c.child and c.child.parents :
                c.render(fd)
            elif end_of_branch :
                c.render(fd)
            else :
                c.rendered = True
        break_it = False
        for target in c.forks :
          if target in pending :
              break_it = True
          elif target.branch :
            if target.branch not in shown_branches :
                shown_branches.append( target.branch , fd , current_branch )
                pending.append( target )
            else :
                  # We just assume that target will appear on pending in the future
                  break_it = True
        if end_of_branch :
            shown_branches.remove( current_branch )
            for c in c.get_childs() :
              if c.branch :
                if c.branch not in shown_branches :
                  shown_branches.append( c.branch , fd , current_branch )
                elif c in pending :
                    pending.remove(c)
                else :
                  # We just assume that target will appear on pending in the future
                  break
                forward_plot(repo, c, pending, fd)
            break
        c = c.child
        if break_it :
            if c :
              if c not in pending :
                pending.append( c )
              else :
                  forward_plot(repo, c, pending, fd)
            break
    else :
        if c.parents :
            if [ p for p in c.get_parents() if not p.rendered ] :
                pending.append(c)
            else :
                c.render( fd , c.parents[0] )
        else :
            c.render(fd)

def chrono_plot ( repo , fd=sys.stdout) :
    """Assumes that commits are properly ordered, so just the commit list is given"""
    first = True
    for c in repo.order :
      if c.branch :
        if not c.parents :
            if first or c.forks or not c.child :
                first = False
                c.render(fd)
            elif c.child and c.child.parents :
                first = True
                c.render(fd)
            if c.child and c.child.branch and c.branch != c.child.branch and c.child.branch not in shown_branches :
                first = True
                shown_branches.append( c.child.branch , fd , c.branch )
        else :
            first = True
            c.render(fd, c.parents[0])
            # Remove branches merged into
            for p in c.parents :
                if p.branch in shown_branches :
                  # The condition below is an ugly hack for some back & forth merge scenarios
                  if not p.branch.is_primary() :
                    shown_branches.remove( p.branch )
        for f in c.forks :
            if f.branch and f.branch not in shown_branches :
                first = True
                shown_branches.append( f.branch , fd , c.branch )


