

import sys

head = """<!DOCTYPE html>
<html>
<body>
<canvas id="gitNetwork"></canvas>
<script src="js/gitnetwork.js"></script>
<script type="text/javascript">
var gitgraph = new GitNetwork();
"""

tail = """</script>
</body>
</html>
"""


def graph ( repo , filename='commits.html' ) :

    fd = open( filename , 'w' )

    fd.write( head )

    shown_branches = [ b for b in repo.branches if b.target() == '<Final>' ]

    for branch in shown_branches :
        branch.render( fd , shown_branches=shown_branches , force=True )

    n = len(repo)
    fd.write( "gitgraph.resize(%d, %d);\n" % ( n+1 , len(shown_branches)+1 ) )

    tails = [ b.end() for b in shown_branches ]
    while tails :
        commit = tails.pop(0)
        backward_plot( repo , commit , tails , fd )

    for branch in shown_branches :
        fd.write( '%s.draw("red");\n' % branch.as_var() )

    fd.write( tail )
    fd.close()

def backward_plot ( repo , commit , pending , fd=sys.stdout ) :
    while commit :
        for c in commit.parents :
            if c.rendered :
                fd.write( "%s.push( %d , %s );\n" % ( commit.branch.as_var() , n , c.branch.as_var() ) )
                commit.rendered = True
                n -= 1
            else :
                pending.append( commit )
                return
        else:
            for c in commit.forks :
                if c.rendered :
                    fd.write( "%s.push( %d , %s );\n" % ( commit.branch.as_var() , n , c.branch.as_var() ) )
                    commit.rendered = True
                    n -= 1
                else :
                    pending.append( commit )
                    return
            else:
                fd.write( "%s.push( %d );\n" % ( commit.branch.as_var() , n ) )
                commit.rendered = True
                n -= 1
        if commit.branch != commit.parent.branch :
            return
        commit = commit.parent

