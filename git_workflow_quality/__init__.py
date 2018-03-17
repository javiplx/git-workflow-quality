
import gitgraphjs

import subprocess
import re
import os


class Commit :

    def __init__ ( self , sha , author , committer , message ) :
        self.sha = sha
        self.author = author
        self.committer = committer
        self.message = message.replace('"', '&quot;' )
        self.parent = None
        self.parents = ()
        self.branch = None
        self.child = None
        self.forks = []

    def set_branch ( self , branch ) :
        if self.branch :
            if self.branch in Repository.primary :
                if branch not in Repository.primary :
                    return
                # self.branch has a higher weight respect to branch
                if Repository.primary.index(self.branch) < Repository.primary.index(branch) :
                    return
            if not branch in Repository.primary and branch != self.branch :
                raise Exception( "cannot assign %s to %s, already owned by %s" % ( branch , self.sha , self.branch ) )
        self.branch = branch

    def set_child ( self , commit ) :
        if self.child :
            raise Exception( "cannot assign %s as child of %s, already parent of %s" % ( sha , self.sha , self.child.sha ) )
        self.child = commit
        self.forks.remove(commit)

    def render ( self , fd , merged_commit=None ) :
        if self.parents :
            fd.write( '%s.merge(%s, {sha1:"%s", message:"%s"});\n' % ( gitgraphjs.js_varname(merged_commit.branch) , gitgraphjs.js_varname(self.branch) , self.sha , self.message ) )
        else :
            fd.write( '%s.commit({sha1:"%s", message:"%s"});\n' % ( gitgraphjs.js_varname(self.branch) , self.sha , self.message ) )

    def __str__ ( self ) :
        parents = " ".join([p.sha for p in self.parents])
        forks = " ".join([f.sha for f in self.forks])
        if self.parent :
            return "%-20s %s : %s/%s %s | %s :: %s" % ( str(self.branch)[:20] , self.sha , self.parent.sha , self.child.sha , parents , forks , self.message )
        return "%-20s %s : %40s/%s %s | %s :: %s" % ( str(self.branch)[:20] , self.sha , '<None>' , self.child.sha , parents , forks , self.message )


class Branch ( list ) :

    def __init__ ( self , branchname ) :
        self.name = branchname
        list.__init__( self )

    def commits ( self ) :
        return [c for c in self if not c.parents]

    def merges ( self ) :
        return [c for c in self if c.parents]

    def stats ( self ) :
        return len(self), len(self.commits()), len(self.merges())

    def begin ( self ) :
        return self[0]

    def end ( self ) :
        return self[-1]

    def source ( self ) :
        source = self.begin().parent
        if not source :
            return '<Initial>'
        return source.branch

    def target ( self ) :
        target = self.end().child
        if not target :
            return '<Final>'
        return target.branch

    def relations ( self ) :
        sources = []
        targets = []
        for c in self :
            for parent in c.parents :
                sources.append( parent.branch )
            for child in c.forks :
                targets.append( child.branch )
        return sources , targets

    def report ( self , branches=False ) :
        output = [ self.name[:25] , len(self.commits()) , len(self.merges()) ]
        if branches :
            sources = self.relations()[0]
            output.extend( ( self.source() , len(sources) , self.target() ) )
        return tuple(output)


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
            if f == "HEAD" : continue
            filename = os.path.join(root, f)
            fd = open(filename)
            branches.append( ( fd.readline()[:-1] , filename[len(heads)+1:].replace('\\', '/') ) )
            fd.close()
    return branches

class Repository ( dict ) :

  primary = ('master', 'develop')

  def __init__ ( self ) :

    self.order = []
    self.branches = {}

    cmd = subprocess.Popen( ['git', 'log', '--all', '--format="%H %ae %ce %s"'] , stdout=subprocess.PIPE )
    line = cmd.stdout.readline()
    while line[:-1] :
        sha , author , committer , message = line[:-1].strip('"').split(None, 3)
        self[sha] = Commit( sha , author , committer , message )
        line = cmd.stdout.readline()

    cmd = subprocess.Popen( ['git', 'log', '--all', '--date-order', '--reverse', '--format="%H %at %ct %P"'] , stdout=subprocess.PIPE )
    line = cmd.stdout.readline()
    while line[:-1] :
        sha , params = line[:-1].strip('"').split(None, 1)
        self.set_params( sha , params.split(None, 4))
        if self[sha].parent and self[sha].parent not in self.order :
            raise Exception( "Incorrect input ordering" )
        self.order.append( self[sha] )
        line = cmd.stdout.readline()

    self.set_childs()

    self.set_branches()

  def set_params ( self , sha , line ) :
      self[sha].author_date = line[0]
      self[sha].committer_date = line[1]
      if len(line) > 2 :
          self[sha].parent = self[line[2]]
          if len(line) > 3 :
              self[sha].parents = [ self[sha1] for sha1 in line[3].split() ]
              if len(self[sha].parents) > 1 :
                  raise Exception( "Octopus merges on %s from %s not handled" % ( self[sha].sha , ", ".join([c.sha for c in self[sha].parents]) ) )

  def branch ( self , branchname ) :
      return self.branches[branchname]

  def events( self ) :
      output = ['']

      multimerged = {}
      for commit in self.values() :
          # Skip if main child is not a merge?
          # Do we really want to skip for primary branches??
          if not commit.forks or not commit.child or commit.branch in self.primary :
              continue
          merges = []
          if commit.child.parents :
              if commit.child.parent != commit :
                  if commit.child.branch == commit.branch :
                      # This is an auto-merge and should be detected somewhere
                      pass
                  else :
                      merges.append( commit.child )
          for F in [f for f in commit.forks if f.parents and f.parent != commit ] :
                  if F.branch == commit.branch :
                      # This is an auto-merge and should be detected somewhere
                      pass
                  else :
                      merges.append( sha )
          if len(merges) > 1 :
              if not multimerged.has_key(len(merges)) :
                  multimerged[len(merges)] = []
              multimerged[len(merges)].append( ( commit.sha , merges ) )
      if multimerged :
          output.append( "Commits with multiple merges" )
          for n in sorted(multimerged.keys()) :
              output.append( "    %3d commits with %2d merges" % ( len(multimerged[n]) , n ) )
          output.append( '' )

      multitarget = 0
      reutilized = 0
      multimerged = 0
      indirect = 0
      multisource = 0
      mergeconflict = 0
      for branch in self.branches.values() :
          if branch.name in self.primary or str(branch.name).startswith('release') :
              continue
          if branch.end().child and branch.end().forks :
              for child in branch.end().forks :
                  if self.branch(child.branch).begin().parent == branch.end() :
                      reutilized += 1
          if branch.end().child and branch.end().parents :
              if branch.end().parents[0] == branch.end().child.parent :
                  mergeconflict += 1
          source = branch.source()
          target = branch.target()
          sources , targets = branch.relations()
          if targets :
              multitarget += 1
          if source in sources :
              multimerged += 1
          if source != target and branch.end().child :
              indirect += 1
          if [ branchname for branchname in sources if branchname != source ] :
              multisource += 1
      output.append( "Branch events" )
      output.append( "  multitarget   %4d" % multitarget )
      output.append( "  reutilized    %4d" % reutilized )
      output.append( "  multimerged   %4d" % multimerged )
      output.append( "  indirect      %4d" % indirect )
      output.append( "  multisource   %4d" % multisource )
      output.append( "  mergeconflict %4d" % mergeconflict )
      output.append( '' )

      return "\n".join(output)

  def report( self , details=False) :
      output = ['']
      output.append( "Number of commits:      %s" % len(self) )
      output.append( "Number of branches:     %s" % ( len(self.branches) - len([b for b in self.branches if b in self.primary]) ) )
      output.append( "# initial commits:      %s" % len([c for c in self.values() if not c.parent ]) )
      output.append( "Number of merges:       %s" % len([c for c in self.values() if c.parents]) )
      output.append( "Ammended commits:       %s" % len([c for c in self.values() if c.author != c.committer and not c.parents]) )
      output.append( "Commits with no branch: %s" % len([c for c in self.values() if not c.branch]) )
      output.append( "Unlabelled heads:       %s" % len([c for c in self.values() if not c.branch and not c.child]) )

      report_fmt = "%25s %8d   %7d    %20s %+03d - %-20s"
      output.append( "" )
      output.append( "%-25s %8s   %7s" % ( 'PRIMARY' , '#commits' , '#merges' ) )
      for branch in Repository.primary :
          if self.branches.has_key(branch) :
              output.append( report_fmt % self.branch(branch).report(True) )

      releases = [ b for b in self.branches if b not in Repository.primary and str(b).startswith('release') ]
      if releases :
          output.append( "" )
          output.append( "%-10s %8s   %7s    (%d branches)" % ( 'RELEASE' , '#commits' , '#merges' , len(releases) ) )
          stats = []
          for release in releases :
              stats.append ( self.branch(release).stats() )
          output.append( "           %8d   %7d" % ( sum([stat[1] for stat in stats]) , sum([stat[2] for stat in stats]) ) )
          L = sum( [ stat[1] for stat in stats ] )
          N = sum( [ 100*stat[1]/stat[0] for stat in stats ] )
          M = sum( [ 100*stat[2]/stat[0] for stat in stats ] )
          output.append( "           %8d%%  %7d%%  ; %6.1f per branch" % ( N/len(stats) , M/len(stats) , float(L) / len(releases) ) )
          if details :
              output.append( "     -----" )
              for release in releases :
                  output.append( report_fmt % self.branch(release).report(True) )
                  commits = self.branch(release)
                  if [c for c in commits if not c.parents] :
                      output[-1] += " *** standard commits (%d)" % len([c for c in commits if not c.parents])

      branches = [ b for b in self.branches if b not in Repository.primary and not str(b).startswith('release') ]
      if branches :
          output.append( "" )
          output.append( "%-10s %8s   %7s   (%d branches)" % ( 'TOPIC' , '#commits' , '#merges' , len(branches) ) )
          stats = []
          for branch in branches :
              stats.append ( self.branch(branch).stats() )
          output.append( "           %8d   %7d" % ( sum([stat[1] for stat in stats]) , sum([stat[2] for stat in stats]) ) )
          L = sum( [ stat[1] for stat in stats ] )
          N = sum( [ 100.0*stat[1]/stat[0] for stat in stats ] )
          M = sum( [ 100.0*stat[2]/stat[0] for stat in stats ] )
          output.append( "           %8d%%  %7d%%  ; %6.1f per branch" % ( N/len(stats) , M/len(stats) , float(L) / len(branches) ) )
          if details :
              output.append( "     -----" )
              for branch in branches :
                  output.append( report_fmt % self.branch(branch).report(True) )

      return "\n".join(output)

  def set_childs ( self ) :

    branches = []
    for commit in self.values() :
      merged = re.search("Merge pull request #(?P<id>[0-9]*) from (?P<repo>[^/]*)/(?P<source>.*)", commit.message )
      if merged :
        if not commit.parents :
          print "WARNING : false merge on %s %s" % ( commit.sha , commit.message )
        else :
          source = merged.group('source').strip("'")
          branches.append( ( commit.parents[0] , source ) )
          commit.parents[0].set_branch( source )
      else :
        merged = re.search("Merge (branch )?(?P<source>[^ ]*) (of [^ ]* )?into (?P<target>[^ ]*)", commit.message)
        if merged :
          if not commit.parents :
            print "WARNING : false merge on %s %s" % ( commit.sha , commit.message )
          else :
            source = merged.group('source').strip("'")
            branches.append( ( commit.parents[0] , source ) )
            commit.parents[0].set_branch(source)
            target = merged.group('target').strip("'")
            branches.append( ( commit.parent , target ) )
            commit.parent.set_branch(target)
        else :
            merged = re.search("Merge remote-tracking branch (?P<source>[^ ]*) into (?P<target>[^ ]*)", commit.message)
            if merged :
                if not commit.parents :
                    print "WARNING : false merge on %s %s" % ( commit.sha , commit.message )
                else :
                    source = merged.group('source').strip("'").replace('origin/', '')
                    branches.append( ( commit.parents[0] , source ) )
                    commit.parents[0].set_branch(source)
                    target = merged.group('target').strip("'")
                    branches.append( ( commit.parent , target ) )
                    commit.parent.set_branch(target)

    for sha,branch in get_branches() :
        branches.append( ( self[sha] , branch ) )
        self[sha].set_branch( branch )

    n = 0
    for commit in self.values() :
        for c in commit.parents :
            if not c.branch :
                n += 1
                newbranch = "branch_%s" % n
                branches.append( ( c , newbranch ) )
                c.set_branch( newbranch )
    if n : print "WARNING : %d removed branch not automatically detected" % n

    # All branches detected at this point

    for c,branch in branches :
        c = c.parent
        while c :
            if not c.parent : # Initial commit detection
                c.set_branch( branch )
                break
            if c.branch and not branch in Repository.primary :
                break
            c.set_branch(branch)
            c = c.parent

    for c in self.values() :
        if c.parent :
            c.parent.forks.append( c )
        for parent in c.parents :
            parent.forks.append( c )

    for c in self.values() :
        if len(c.forks) == 1 :
            c.set_child( c.forks[0] )
        elif len(c.forks) > 1 :
            child = [ f for f in c.forks if f.branch == c.branch ]
            if child :
                 c.set_child( child[0] )
            else :
                 c.set_child( sorted(c.forks, key=lambda x : x.committer_date)[0] )

  def set_branches ( self ) :

      for commit in self.order :
          if not self.branches.has_key( commit.branch ) :
              self.branches[commit.branch] = Branch(commit)
          self.branch(commit.branch).append( commit )

