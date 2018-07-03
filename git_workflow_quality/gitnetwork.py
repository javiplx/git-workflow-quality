

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
            self.push( branch )

    def push ( self , branch ) :
        dict.__setitem__( self , branch , branch.end() )
        self.fd.write( 'var %s = gitgraph.branch({"name":"%s", "column":%d});\n' % ( branch.as_var() , branch , len(self) ) )

    def resize ( self , n ) :
        self.ptr = n
        self.fd.write( "gitgraph.resize(%d, %d);\n" % ( self.ptr+1 , len(self)+1 ) )

    def unfinished ( self ) :
        unknowns = []

        for branch in self :
            if not self[branch] : continue
            unknowns.extend( [ c.branch for c in self[branch].get_childs(False) if c.branch not in self ] )
            childrens = [ c.branch.name for c in self[branch].get_childs(False) if not self.get(c.branch) ]
            self.fd.write( '%s.push(["%s"]);\n' % ( branch.as_var() , '","'.join(childrens) ) )
            self[branch].rendered = True
            self.fd.write( '%s.draw("red");\n' % branch.as_var() )
            self[branch] = None

        for branch in unknowns :
            self.push( branch )

        return unknowns

    def close ( self ) :
        while self.unfinished() :
            self.fd.write( "gitgraph.pointer -= 10;\n" )
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

    first = True
    while commit :

        if [ c for c in commit.get_childs(False) if not c.rendered ] : return

        if commit.get_childs(False) :
            childrens = [ c.branch for c in commit.get_childs(False) ]
            fd.write( '%s.push(["%s"]);\n' % ( commit.branch.as_var() , '","'.join(map(str,childrens)) ) )
            first = True
        else :
            if first or commit.branch.begin() == commit :
                fd.write( "%s.push([]);\n" % commit.branch.as_var() )
            if commit.branch.target() != commit :
                first = False
        commit.rendered = True

        for c in commit.get_parents(False) :
            if c.branch not in pending :
                pending.push( c.branch )

        if not commit.parent :
            fd.write( '%s.draw();\n' % commit.branch.as_var() )
        elif commit.branch != commit.parent.branch :
            fd.write( '%s.draw();\n' % commit.branch.as_var() )
            pending[commit.branch] = None
            break

        pending[commit.branch] = commit.parent
        commit = commit.parent

