
import git_workflow_quality

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
        self._rows = [ repo.get_branch(name) for name in git_workflow_quality.Repository.primary ]
        self.reserved = len(self._rows)
        self.HEAD = None
        for branch in repo.branches :
            if branch.target() != '<Final>' : continue
            self.push( branch , True )

    def pop ( self , key ) :
       idx = self._rows.index(key)
       self._rows[idx] = None

    def __setitem__ ( self , key , value ) :
        if key not in self._rows :
            if None in self._rows[self.reserved:] :
                idx = self.reserved + self._rows[self.reserved:].index(None)
                self._rows[idx] = key
            else :
                self._rows.append( key )
        dict.__setitem__( self , key , value )

    def row ( self , branch ) :
        return self._rows.index(branch) + 1

    def push ( self , branch , opened=False ) :
        self[branch] = branch.end()
        self.fd.write( 'var %s = gitgraph.branch({"name":"%s", "column":%d, "open":%s});\n' % ( branch.as_var() , branch , self.row(branch) , str(opened).lower() ) )

    def unfinished ( self ) :
        unknowns = []

        for branch in self :
            if not self[branch] : continue
            unknowns.extend( [ c.branch for c in self[branch].get_childs(False) if c.branch not in self ] )
            self.fd.write( '%s.push("%s",[]);\n' % ( branch.as_var() , branch.begin().sha[:8] ) )
            for c in self[branch].get_childs(False) :
                if self.get(c.branch) : continue
                self.fd.write( '%s.head().addChild("%s");\n' % ( branch.as_var() , c.sha[:8] ) )
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


def graph ( repo , args , filename='commits.html' ) :

    repo.graphed = args.limit

    shown_branches = canvas( repo , filename )

    while [ b for b in shown_branches.values() if b ] and repo.graphed > 0 :
        for commit in [ b for b in shown_branches.values() if b ] :
            backward_plot( repo , commit , shown_branches , shown_branches.fd )

    if args.limit > 0 and repo.graphed <= 0 :
        print "\nOnly around %d%% commits shown in graph" % ( 100.0 * args.limit / len(repo) )

    shown_branches.close()

def backward_plot ( repo , commit , pending , fd=sys.stdout ) :

    first = True
    while commit :

        for c in commit.get_parents(False) :
            if c.branch not in pending :
                pending.push( c.branch )

        if [ c for c in commit.get_childs(False) if not c.rendered ] : return

        if commit.branch.end() == commit and commit.child == pending.HEAD :
            fd.write( 'gitgraph.pointer -= 2;\n' )

        if commit.get_childs(False) :
            fd.write( '%s.push("%s",[]);\n' % ( commit.branch.as_var() , commit.sha[:8] ) )
            for c in commit.get_childs(False) :
                if c.branch.begin() == c :
                    fd.write( '%s.get("%s").addChild("%s"); // begin\n' % ( c.branch.as_var() , c.sha[:8] , commit.sha[:8] ) )
                else :
                    fd.write( '%s.head().addChild("%s"); // standar\n' % ( commit.branch.as_var() , c.sha[:8] ) )
            if not pending[c.branch] and c.branch in pending._rows:
                pending.pop(c.branch)
            first = True
        else :
            if commit.parents or commit.branch.begin() == commit :
                first = True
            if first :
                fd.write( '%s.push("%s",[]);\n' % ( commit.branch.as_var() , commit.sha[:8] ) )
                repo.graphed -= 1
            if not commit.parents :
                first = False
        pending.HEAD = commit
        commit.rendered = True

        if commit.parent and commit.branch != commit.parent.branch :
            pending[commit.branch] = None
            break

        pending[commit.branch] = commit.parent
        commit = commit.parent

