

import sys

head = """<!DOCTYPE html>
<html>
<body>
<canvas id="gitNetwork"></canvas>
<script src="js/gitnetwork.js"></script>
<script type="text/javascript">
var gitnetwork = new GitNetwork();
"""

tail = """</script>
</body>
</html>
"""


def graph ( repo , filename='commits.html' ) :

    fd = open( filename , 'w' )

    fd.write( head )

    tails = [ b for b in repo.branches if b.target() == '<Final>' ]

    n = len(repo)
    for branch in tails :
        fd.write( 'var %s = gitnetwork.branch("%s", %d);\n' % ( branch.as_var() , branch, tails.index(branch)+1 ) )
        for commit in branch.commits() :
            fd.write( "%s.push( %d );\n" % ( branch.as_var() , n ) )
            n -= 1
        fd.write( '%s.draw("red");\n' % branch.as_var() )

    fd.write( tail )
    fd.close()

