

import sys

class canvas ( dict ) :

    head = """<!DOCTYPE html>
<html>
<body>
<canvas id="gitNetwork"></canvas>
<script src="js/gitnetwork.js"></script>
<script type="text/javascript">
var gitgraph = new GitNetwork(%d);
"""

    tail = """</script>
</body>
</html>
"""

    def __init__ ( self , repo , filename='commits.html' ) :
        self.fd = open( filename , 'w' )
        self.fd.write( self.head % len(repo) )
        dict.__init__( self )
        for branch in repo.branches :
            if branch.target() != '<Final>' : continue
            self.push( branch )

    def push ( self , branch ) :
        dict.__setitem__( self , branch , branch.end() )
        self.fd.write( 'var %s = gitgraph.branch({"name":"%s", "column":%d});\n' % ( branch.as_var() , branch , len(self) ) )

    def unfinished ( self ) :
        unknowns = []

        for branch in self :
            if not self[branch] : continue
            unknowns.extend( [ c.branch for c in self[branch].get_childs(False) if c.branch not in self ] )
            childrens = [ c for c in self[branch].get_childs(False) if not self.get(c.branch) ]
            self.fd.write( '%s.push("%s",["%s"]);\n' % ( branch.as_var() , branch.begin().sha[:8] , '","'.join( [ c.sha[:8] for c in childrens ] ) ) )
            self[branch].rendered = True
            self.fd.write( '%s.color = "red";\n' % branch.as_var() )
            self[branch] = None

        for branch in unknowns :
            self.push( branch )

        return unknowns

    def close ( self ) :
        while self.unfinished() :
            self.fd.write( "gitgraph.pointer -= 10;\n" )
        self.fd.write( 'gitgraph.draw();\n' )
        self.fd.write( self.tail )
        self.fd.close()


def graph ( repo , filename='commits.html' ) :

    shown_branches = canvas( repo , filename )

    while [ b for b in shown_branches.values() if b ] :
        for commit in [ b for b in shown_branches.values() if b ] :
            backward_plot( repo , commit , shown_branches , shown_branches.fd )

    shown_branches.close()

def backward_plot ( repo , commit , pending , fd=sys.stdout ) :

    first = True
    while commit :

        if [ c for c in commit.get_childs(False) if not c.rendered ] : return

        if commit.get_childs(False) :
            fd.write( '%s.push("%s",["%s"]);\n' % ( commit.branch.as_var() , commit.sha[:8] , '","'.join( [ c.sha[:8] for c in commit.get_childs(False) ] ) ) )
            first = True
        else :
            if first or commit.branch.begin() == commit  or True :
                fd.write( '%s.push("%s",[]);\n' % ( commit.branch.as_var() , commit.sha[:8] ) )
            if commit.branch.target() != commit :
                first = False
        commit.rendered = True

        for c in commit.get_parents(False) :
            if c.branch not in pending :
                pending.push( c.branch )

        if commit.parent and commit.branch != commit.parent.branch :
            pending[commit.branch] = None
            break

        pending[commit.branch] = commit.parent
        commit = commit.parent

