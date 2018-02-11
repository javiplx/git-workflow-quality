
import subprocess

class commit :

    def __init__ ( self , sha , author , committer , message ) :
        self.sha = sha
        self.author = author
        self.committer = committer
        self.message = message.replace('"', '&quot;' )

    def set_params ( self , line ) :
        self.author_date = line[0]
        self.committer_date = line[1]
        self.parent = None
        self.parents = ()
        self.branch = ''
        if len(line) > 2 :
            self.parent = line[2]
            if len(line) > 3 :
                self.parents = line[3].split()
                if len(self.parents) > 1 :
                    raise Exception( "Octopus merges on %s from %s not handled" % ( self.sha , ", ".join(self.parents) ) )
        else : # This trick is required to assign a branch to the initial commit and should be revised
            self.set_branch('master')
        self.child = None
        self.forks = []

    def set_branch ( self , branch ) :
        if self.branch :
            raise Exception( "cannot assign %s to %s, already owned by %s" % ( branch , self.sha , self.branch ) )
        self.branch = branch

    def set_child ( self , sha ) :
        if self.branch == commits[sha].branch :
            if self.child :
                raise Exception( "cannot assign %s as child of %s, already parent of %s" % ( sha , self.sha , self.child ) )
            self.child = sha
        else :
            self.forks.append(sha)

    def __str__ ( self ) :
        parents = " ".join(self.parents)
        forks = " ".join(self.forks)
        if self.parent :
            return "%-20s %s : %s/%s %s | %s :: %s" % ( self.branch[:20] , self.sha , self.parent , self.child , parents , forks , self.message )
        return "%-20s %s : %40s/%s %s | %s :: %s" % ( self.branch[:20] , self.sha , '<None>' , self.child , parents , forks , self.message )


def get_commits () :

    commits = {}
    order = []

    cmd = subprocess.Popen( 'git log --all --format="%H %ae %ce %s"' , stdout=subprocess.PIPE )
    line = cmd.stdout.readline()
    while line[:-1] :
        sha , author , committer , message = line[:-1].split(None, 3)
        commits[sha] = commit( sha , author , committer , message )
        line = cmd.stdout.readline()

    order = []

    cmd = subprocess.Popen( 'git log --all --date-order --reverse --format="%H %at %ct %P"' , stdout=subprocess.PIPE )
    line = cmd.stdout.readline()
    while line[:-1] :
        sha , params = line[:-1].split(None, 1)
        commits[sha].set_params(params.split(None, 4))
        if commits[sha].parent and commits[sha].parent not in order :
            raise Exception( "Incorrect input ordering" )
        order.append( sha )
        line = cmd.stdout.readline()

    return commits , order


def set_branches ( commits ) :
    for c in commits.values() :
        if c.parent :
            commits[c.parent].forks.append( c.sha )
        for parent in c.parents :
            commits[parent].forks.append( c.sha )
    n = 1
    for commit in [ c for c in commits.values() if not c.forks ] :
        commit.set_branch( "branch_%s" % n )
        n += 1

