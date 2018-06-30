

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

        if [ c for c in commit.get_childs(False) if not c.rendered ] : return
        if [ c for c in commit.get_parents(False) if c not in pending.values() ] : return

        for c in commit.get_parents(False) :
            for b in c.get_childs(False) :
                if commit.branch == b.branch : continue
                if not b.rendered: return
        for c in commit.get_parents(False) :
            dict.__setitem__( pending , c.branch , c.parent )
            fd.write( "%s.push( %d );\n" % ( c.branch.as_var() , pending.ptr-1 ) )
            c.rendered = True

        if commit.get_parents(False) :
            fd.write( "%s.push( %d , %s );\n" % ( commit.branch.as_var() , pending.ptr, c.branch.as_var() ) )
        else :
            fd.write( "%s.push( %d );\n" % ( commit.branch.as_var() , pending.ptr ) )
        commit.rendered = True

        for c in commit.get_parents(False) :
            pending.ptr -= 1
        pending.ptr -= 1

        if not commit.parent :
            fd.write( '%s.draw("cyan");\n' % commit.branch.as_var() )
        elif commit.branch != commit.parent.branch :
            if [ c for c in commit.get_parents() if not c.rendered ] : return
            fd.write( '%s.draw("green");\n' % commit.branch.as_var() )
            pending[commit.branch] = None
            break

        pending[commit.branch] = commit.parent
        commit = commit.parent

