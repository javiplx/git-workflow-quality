
import subprocess
import re
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
            if self.branch in repository.primary :
                return
            if not branch in repository.primary and branch != self.branch :
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


def get_branches () :
    branches = []
    refs = "refs/heads"
    info = "info/refs"
    heads = "refs/heads"
    if os.path.isdir(".git") :
        refs = "refs/remotes/origin"
        info = os.path.join( ".git" , info )
        heads = os.path.join( ".git" , refs )
    if os.path.isfile(info) :
        with open(info) as fd :
            line = fd.readline()
            while line[:-1] :
                items = line[:-1].split(None, 2)
                if items[1].startswith(refs) :
                    branches.append( ( items[0] , items[1][len(refs)+1:] ) )
                line = fd.readline()
    for root, dirs, files in os.walk(heads) :
        for f in files:
            filename = os.path.join(root, f)
            fd = open(filename)
            branches.append( ( fd.readline()[:-1] , filename[len(heads)+1:].replace('\\', '/') ) )
            fd.close()
    return branches

class repository :

  primary = ('master', 'develop')

  def __init__ ( self ) :

    self.commits = {}
    self.order = []

    cmd = subprocess.Popen( ['git', 'log', '--all', '--format="%H %ae %ce %s"'] , stdout=subprocess.PIPE )
    line = cmd.stdout.readline()
    while line[:-1] :
        sha , author , committer , message = line[:-1].strip('"').split(None, 3)
        self.commits[sha] = commit( sha , author , committer , message )
        line = cmd.stdout.readline()

    cmd = subprocess.Popen( ['git', 'log', '--all', '--date-order', '--reverse', '--format="%H %at %ct %P"'] , stdout=subprocess.PIPE )
    line = cmd.stdout.readline()
    while line[:-1] :
        sha , params = line[:-1].strip('"').split(None, 1)
        self.commits[sha].set_params(params.split(None, 4))
        if self.commits[sha].parent and self.commits[sha].parent not in self.order :
            raise Exception( "Incorrect input ordering" )
        self.order.append( sha )
        line = cmd.stdout.readline()

    self.set_childs()


  def report( self ) :
      output = []
      output.append( "Number of commits: %s" % len(self.commits) )
      output.append( "# initial commits: %s" % len([c for c in self.commits.values() if not c.parent ]) )
      output.append( "Number of merges:  %s" % len([c for c in self.commits.values() if c.parents]) )
      output.append( "Ammended commits:  %s" % len([c for c in self.commits.values() if c.author != c.committer and not c.parents]) )
      output.append( "Unlabelled heads:  %s" % len([c for c in self.commits.values() if not c.branch and not c.child]) )
      output.append( "" )
      output.append( "branch group   #commits   #merges" )
      output.append( "primary        %8d   %7d" % ( len([c for c in self.commits.values() if not c.parents and c.branch in repository.primary]) , len([c for c in self.commits.values() if c.parents and c.branch in repository.primary]) ) )
      output.append( "topic          %8d   %7d" % ( len([c for c in self.commits.values() if not c.parents and c.branch not in repository.primary]) , len([c for c in self.commits.values() if c.parents and c.branch not in repository.primary]) ) )
      return "\n".join(output)

  def set_childs ( self ) :

    branches = []
    for commit in self.commits.values() :
      merged = re.search("Merge pull request #(?P<id>[0-9]*) from (?P<repo>[^/]*)/(?P<source>.*)", commit.message )
      if merged :
        if not commit.parents :
          print "WARNING : false merge on %s %s" % ( commit.sha , commit.message )
        else :
          source = merged.group('source').strip("'")
          branches.append( ( commit.parents[0] , source ) )
          self.commits[commit.parents[0]].set_branch( source )
      else :
        merged = re.search("Merge branch (?P<source>[^ ]*) (of [^ ]* )?into (?P<target>[^ ]*)", commit.message)
        if merged :
          if not commit.parents :
            print "WARNING : false merge on %s %s" % ( commit.sha , commit.message )
          else :
            source = merged.group('source').strip("'")
            branches.append( ( commit.parents[0] , source ) )
            self.commits[commit.parents[0]].set_branch(source)
            target = merged.group('target').strip("'")
            branches.append( ( commit.parent , target ) )
            self.commits[commit.parent].set_branch(target)

    for sha,branch in get_branches() :
        branches.append( ( sha , branch ) )
        self.commits[sha].set_branch( branch )

    n = 0
    for commit in self.commits.values() :
        for parent in commit.parents :
            c = self.commits[parent]
            if not c.branch :
                n += 1
                newbranch = "branch_%s" % n
                branches.append( ( c.sha , newbranch ) )
                c.set_branch( newbranch )
    if n : print "WARNING : %d removed branch not automatically detected" % n

    # All branches detected at this point

    for sha,branch in branches :
        commit = self.commits[sha]
        c = self.commits[commit.parent]
        while c :
            if not c.parent : # Initial commit detection
                c.set_branch( branch )
                break
            if c.branch and not branch in repository.primary :
                break
            c.set_branch(branch)
            c = self.commits[c.parent]

    for c in self.commits.values() :
        if c.parent :
            self.commits[c.parent].forks.append( c.sha )
        for parent in c.parents :
            self.commits[parent].forks.append( c.sha )

    for c in self.commits.values() :
        if len(c.forks) == 1 :
            c.set_child( c.forks[0] )
        elif len(c.forks) > 1 :
            child = [ sha for sha in c.forks if self.commits[sha].branch == c.branch ]
            if child :
                 c.set_child( child[0] )

