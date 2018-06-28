

import sys

class canvas ( dict ) :

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

    def __init__ ( self , branches , filename='commits.html' ) :
        self.fd = open( filename , 'w' )
        self.fd.write( self.head )
        dict.__init__( self )
        for branch in branches :
            dict.__setitem__( self , branch , branch.end() )
            self.fd.write( 'var %s = gitgraph.branch({"name":"%s", "column":%d});\n' % ( branch.as_var() , branch , len(self) ) )

    def resize ( self , n ) :
        self.ptr = n
        self.fd.write( "gitgraph.resize(%d, %d);\n" % ( self.ptr+1 , len(self)+1 ) )

    def close ( self ) :
        for branch in self :
            self.fd.write( "%s.push( %d );\n" % ( branch.as_var() , self.ptr ) )
            self[branch].rendered = True
            self.fd.write( '%s.draw("red");\n' % branch.as_var() )
        self.fd.write( self.tail )
        self.fd.close()


def graph ( repo , filename='commits.html' ) :

    shown_branches = canvas( [ b for b in repo.branches if b.target() == '<Final>' ] , filename )
    shown_branches.resize( len(repo) )

    tails = [ b.end() for b in shown_branches ]
    while tails :
        commit = tails.pop(0)
        backward_plot( repo , commit , tails , shown_branches.fd )

    shown_branches.close()

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

