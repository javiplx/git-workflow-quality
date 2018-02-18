
import subprocess

import os


primary = ('master', 'develop')

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
        self.child = None
        self.forks = []

    def set_branch ( self , branch ) :
        if self.branch :
            if self.branch in primary :
                return
            raise Exception( "cannot assign %s to %s, already owned by %s" % ( branch , self.sha , self.branch ) )
        self.branch = branch

    def set_child ( self , sha ) :
        if self.child :
            raise Exception( "cannot assign %s as child of %s, already parent of %s" % ( sha , self.sha , self.child ) )
        self.child = sha
        self.forks.remove(sha)

    def __str__ ( self ) :
        parents = " ".join(self.parents)
        forks = " ".join(self.forks)
        if self.parent :
            return "%-20s %s : %s/%s %s | %s :: %s" % ( self.branch[:20] , self.sha , self.parent , self.child , parents , forks , self.message )
        return "%-20s %s : %40s/%s %s | %s :: %s" % ( self.branch[:20] , self.sha , '<None>' , self.child , parents , forks , self.message )


def get_commits () :

    commits = {}

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

    set_childs ( commits , order )

    return commits , order


def get_branches () :
    branches = {}
    if os.path.isfile(".git/info/refs") :
        with open(".git/info/refs") as fd :
            line = fd.readline()
            while line[:-1] :
                items = line[:-1].split(None, 2)
                if items[1].startswith('refs/heads/') :
                    branches[items[0]] = items[1][11:]
                line = fd.readline()
    for root, dirs, files in os.walk(".git/refs/heads") :
        for f in files:
            filename = os.path.join(root, f)
            fd = open(filename)
            branches[fd.readline()[:-1]] = filename[16:]
            fd.close()
    return branches

def set_childs ( commits , order ) :

    for c in commits.values() :
        if c.parent :
            commits[c.parent].forks.append( c.sha )
        for parent in c.parents :
            commits[parent].forks.append( c.sha )

    branches = get_branches()

    branchnames = dict([ (branches[key],key) for key in branches ])

    for branch in primary :
        if not branchnames.has_key(branch) :
            continue
        commit = commits[branchnames[branch]]
        c = commits[commit.parent]
        while c :
            if not c.parent : # Initial commit detection
                c.set_branch( branch )
                break
            if c.branch :
                break
            c.set_branch(branch)
            c = commits[c.parent]

    for sha in branches :
        commits[sha].set_branch( branches[sha] )

    order.reverse()

    for sha in order :
        c = commits[sha]
        if not c.parents or commits[c.parents[0]].branch : continue
        idx = c.message.find( "Merge branch '" )
        if idx != -1 :
            branch_name = c.message[idx+14:]
            idx = branch_name.find( "'" )
            branch = branch_name[:idx] + " (?)"
            c = commits[c.parents[0]]
            if branch not in branches.values() :
                branches[c.sha] = branch
                while c :
                    if not c.parent or c.branch :
                        break
                    c.set_branch(branch)
                    c = commits[c.parent]
            else :
                idx = branch_name.find( "' into '" )
                branch_name = branch_name[idx+8:]
                idx = branch_name.find( "'" )
                branch = branch_name[:idx] + " (?)"
                if branch not in branches.values() :
                    branches[c.sha] = branch
                    while c :
                        if c.branch :
                            break
                        c.set_branch(branch)
                        c = commits[c.parent]

    n = 1
    for commit in commits.values() :
        if commit.forks or commit.branch :
            continue
        commit.set_branch( "branch_%s" % n )
        if branches.has_key(commit.sha) and branches[commit.sha] != commit.branch :
            raise Exception( "Rewriting %s from branch %s to %s" % ( commit.sha , branches[commit.sha] , commit.brach ) )
        branches[commit.sha] = commit.branch
        n += 1

    for sha,branch in branches.iteritems() :
        commit = commits[sha]
        c = commits[commit.parent]
        while c :
            if not c.parent : # Initial commit detection
                c.set_branch( branch )
                break
            if c.branch :
                break
            c.set_branch(branch)
            c = commits[c.parent]

    for c in commits.values() :
        if len(c.forks) == 1 :
            c.set_child( c.forks[0] )
        elif len(c.forks) > 1 :
            child = [ sha for sha in c.forks if commits[sha].branch == c.branch ]
            if child :
                 c.set_child( child[0] )

