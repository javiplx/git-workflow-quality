

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
            if not self[branch] : continue
            self.fd.write( "%s.push( %d );\n" % ( branch.as_var() , self.ptr ) )
            self[branch].rendered = True
            self.fd.write( '%s.draw("red");\n' % branch.as_var() )
        self.fd.write( self.tail )
        self.fd.close()


def graph ( repo , filename='commits.html' ) :

    shown_branches = canvas( [ b for b in repo.branches if b.target() == '<Final>' ] , filename )
    shown_branches.resize( len(repo) )

    while [ b for b in shown_branches.values() if b ] :
        for commit in [ b for b in shown_branches.values() if b ] :
            backward_plot( repo , commit , shown_branches , shown_branches.fd )

    shown_branches.close()

def backward_plot ( repo , commit , pending , fd=sys.stdout ) :

    while commit :

        if [ c for c in commit.forks if c.branch and not c.rendered ] : return

        for c in commit.parents :
            if not c.branch in pending.keys() :
                dict.__setitem__( pending , c.branch , c )
                fd.write( 'var %s = gitgraph.branch({"name":"%s", "column":%d});\n' % ( c.branch.as_var() , c.branch , len(pending) ) )

        fd.write( "%s.push( %d );\n" % ( commit.branch.as_var() , pending.ptr ) )
        commit.rendered = True
        pending.ptr -= 1

        children = [ b for b in commit.forks if b.branch ]
        if children :
            pending.ptr -= 1
            for c in children :
                fd.write( "%s.push( %d , %s );\n" % ( c.branch.as_var() , pending.ptr+3 , commit.branch.as_var() ) )
                c.rendered = True
                if [ b for b in c.get_parents() if not b.rendered ] : continue
                if c.branch.begin() == c :
                    fd.write( '%s.draw("green");\n' % c.branch.as_var() )
                    pending[c.branch] = None
                else :
                    pending[c.branch] = c.parent

        if not commit.parent :
            fd.write( '%s.draw("cyan");\n' % commit.branch.as_var() )
        elif commit.branch != commit.parent.branch :
            if [ c for c in commit.get_parents() if not c.rendered ] : return
            if pending[commit.parent.branch] and commit.parent not in pending.values() :
                fd.write( '%s.draw("blue");\n' % commit.parent.branch.as_var() )
            return

        pending[commit.branch] = commit.parent
        commit = commit.parent
