
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
        self.rendered = False

    def set_branch ( self , branch ) :
        if branch < self.branch :
            # self.branch has a higher weight respect to branch
            return
        if self.branch and not branch.is_primary() :
            print "WARNING : cannot assign %s to %s, already owned by %s" % ( branch , self.sha , self.branch )
            return
        branch.append( self )

    def set_child ( self , commit ) :
        if self.child :
            raise Exception( "cannot assign %s as child of %s, already parent of %s" % ( sha , self.sha , self.child.sha ) )
        self.child = commit
        self.forks.remove(commit)

    def get_parents ( self ) :
        parents = []
        if self.parent :
            parents.append( self.parent )
        parents.extend( self.parents )
        return parents

    def get_childs ( self ) :
        childs = []
        if self.child :
            childs.append( self.child )
        childs.extend( self.forks )
        return childs

    def render ( self , fd , merged_commit=None ) :
        if self.parents :
            fd.write( '%s.merge(%s, {sha1:"%s", message:"%s"});\n' % ( merged_commit.branch.as_var() , self.branch.as_var() , self.sha , self.message ) )
        else :
            fd.write( '%s.commit({sha1:"%s", message:"%s"});\n' % ( self.branch.as_var() , self.sha , self.message ) )
        self.rendered = True

    def __str__ ( self ) :
        parents = " ".join([p.sha for p in self.parents])
        child =  self.child and self.child.sha or '<None>'
        forks = " ".join([f.sha for f in self.forks])
        if self.parent :
            return "%-20s %s : %s/%s %s | %s :: %s" % ( str(self.branch)[:20] , self.sha , self.parent.sha , child , parents , forks , self.message )
        return "%-20s %s : %40s/%s %s | %s :: %s" % ( str(self.branch)[:20] , self.sha , '<None>' , child , parents , forks , self.message )


class Branch ( list ) :

    primary = ('master', 'develop')

    def __init__ ( self , branchname , orphan=False ) :
        self.name = branchname
        self.orphan = orphan
        self.rendered = False
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
        return source.branch.name

    def target ( self ) :
        target = self.end().child
        if not target or not target.branch :
            return '<Final>'
        return target.branch.name

    def is_primary ( self ) :
        return self.name in Branch.primary

    def is_release ( self ) :
        return self.name.startswith('release')

    def is_orphan ( self ) :
        return self.orphan

    def __lt__ ( self , other ) :
        if not other :
            return False
        if self == other :
            return True
        if self.is_primary() and other.is_primary() :
            return Branch.primary.index(other.name) < Branch.primary.index(self.name)
        if other.is_primary() :
            return True
        return False

    def append ( self , commit ) :
        if commit.branch :
            commit.branch.remove( commit )
        list.append( self , commit )
        commit.branch = self

    def __str__ ( self ) :
        return self.name

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

    def as_var ( self ) :
        return "branch_" + self.name.replace(' (2)','_duplicated').replace('/', '_slash_' ).replace('-', '_dash_').replace('.', '_dot_').replace(' ', '_white_').replace(':', '_colon_')

    def render ( self , fd , parent=None , shown_branches=None ) :
        if self.is_primary() :
            column = Branch.primary.index(self.name)
        else :
            column = shown_branches.index(self)
        json = 'name:"%s", column:%d' % ( self , column )
        if parent :
            fd.write( 'var %s = %s.branch({%s});\n' % ( self.as_var() , parent.as_var() , json ) )
        else :
            fd.write( 'var %s = gitgraph.branch({%s});\n' % ( self.as_var() , json ) )
        self.rendered = True


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

  def set_params ( self , sha , line ) :
      self[sha].author_date = int(line[0])
      self[sha].committer_date = int(line[1])
      if len(line) > 2 :
          self[sha].parent = self[line[2]]
          if len(line) > 3 :
              self[sha].parents = [ self[sha1] for sha1 in line[3].split() ]
              if len(self[sha].parents) > 1 :
                  raise Exception( "Octopus merges on %s from %s not handled" % ( self[sha].sha , ", ".join([c.sha for c in self[sha].parents]) ) )

  def new_branch ( self , branchname , orphan=False ) :
      if self.branches.has_key( branchname ) :
          if not self.branches[branchname].is_primary() :
              return self.new_branch( "%s (2)" % branchname , orphan )
      else :
          self.branches[branchname] = Branch(branchname, orphan)
      return self.branches[branchname]

  def events( self ) :
      output = ['']

      multimerged = {}
      for commit in self.values() :
          # Skip if main child is not a merge?
          # Do we really want to skip for primary branches??
          if not commit.forks or not commit.child or ( commit.branch and commit.branch.is_primary() ) :
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
                      merges.append( F )
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
          if branch.is_primary() or branch.is_release() :
              continue
          if branch.end().child and branch.end().forks :
              for child in branch.end().forks :
                if child.branch and child.branch.begin() :
                  if child.branch.begin().parent == branch.end() :
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
      output.append( "Number of commits:  %s" % len(self) )
      output.append( "Number of branches: %s" % ( len(self.branches) - len([b for b in self.branches.values() if b.is_primary()]) ) )
      output.append( "# initial commits:  %s" % len([c for c in self.values() if not c.parent ]) )
      output.append( "Number of merges:   %s" % len([c for c in self.values() if c.parents]) )
      output.append( "Ammended commits:   %s" % len([c for c in self.values() if c.author != c.committer and not c.parents]) )
      output.append( "# orphan commits    %s" % len([c for c in self.values() if c.branch.is_orphan()]) )
      output.append( "Unlabelled heads:   %s" % len([c for c in self.values() if not c.branch and not c.child]) )

      empty = [ self.branches.pop(b.name) for b in self.branches.values() if len(b) == 0 ]
      if empty :
          output.append( "" )
          output.append( "Branches without commits (%s)" % len(empty) )
          for branchname in empty :
              output.append( " * %s" % branchname )

      report_fmt = "%25s %8d   %7d    %20s %+03d - %-20s"
      output.append( "" )
      output.append( "%-25s %8s   %7s" % ( 'PRIMARY' , '#commits' , '#merges' ) )
      for branch in [ b for b in self.branches.values() if b.is_primary() ] :
          output.append( report_fmt % branch.report(True) )

      releases = [ b for b in self.branches.values() if b.is_release() ]
      if releases :
          output.append( "" )
          output.append( "%-10s %8s   %7s    (%d branches)" % ( 'RELEASE' , '#commits' , '#merges' , len(releases) ) )
          stats = []
          for release in releases :
              stats.append( release.stats() )
          output.append( "           %8d   %7d" % ( sum([stat[1] for stat in stats]) , sum([stat[2] for stat in stats]) ) )
          L = sum( [ stat[1] for stat in stats ] )
          N = sum( [ 100*stat[1]/stat[0] for stat in stats ] )
          M = sum( [ 100*stat[2]/stat[0] for stat in stats ] )
          output.append( "           %8d%%  %7d%%  ; %6.1f per branch" % ( N/len(stats) , M/len(stats) , float(L) / len(releases) ) )
          if details :
              output.append( "     -----" )
              for release in releases :
                  output.append( report_fmt % release.report(True) )
                  commits = self.branches[release]
                  if [c for c in commits if not c.parents] :
                      output[-1] += " *** standard commits (%d)" % len([c for c in commits if not c.parents])

      branches = [ b for b in self.branches.values() if not b.is_primary() and not b.is_release() ]
      if branches :
          output.append( "" )
          output.append( "%-10s %8s   %7s   (%d branches)" % ( 'TOPIC' , '#commits' , '#merges' , len(branches) ) )
          stats = []
          for branch in branches :
              stats.append ( branch.stats() )
          output.append( "           %8d   %7d" % ( sum([stat[1] for stat in stats]) , sum([stat[2] for stat in stats]) ) )
          L = sum( [ stat[1] for stat in stats ] )
          N = sum( [ 100.0*stat[1]/stat[0] for stat in stats ] )
          M = sum( [ 100.0*stat[2]/stat[0] for stat in stats ] )
          output.append( "           %8d%%  %7d%%  ; %6.1f per branch" % ( N/len(stats) , M/len(stats) , float(L) / len(branches) ) )
          if details :
              output.append( "     -----" )
              for branch in branches :
                  output.append( report_fmt % branch.report(True) )

      return "\n".join(output)

  def set_childs ( self ) :

    branches = []
    for commit in self.values() :
      merged = re.search("Merge pull request #(?P<id>[0-9]*) from (?P<repo>[^/]*)/(?P<source>.*)", commit.message )
      if merged :
        if not commit.parents :
          print "WARNING : false merge on %s %s" % ( commit.sha , commit.message )
        else :
          source = self.new_branch(merged.group('source').strip("'"))
          branches.append( ( commit.parents[0] , source ) )
          commit.parents[0].set_branch( source )
      else :
        merged = re.search("Merge (branch )?(?P<source>[^ ]*) (of [^ ]* )?into (?P<target>[^ ]*)", commit.message)
        if merged :
          if not commit.parents :
            print "WARNING : false merge on %s %s" % ( commit.sha , commit.message )
          else :
            source = self.new_branch(merged.group('source').strip("'"))
            branches.append( ( commit.parents[0] , source ) )
            commit.parents[0].set_branch(source)
            target = self.new_branch(merged.group('target').strip("'"))
            branches.append( ( commit.parent , target ) )
            commit.parent.set_branch(target)
        else :
            merged = re.search("Merge remote-tracking branch (?P<source>[^ ]*) into (?P<target>[^ ]*)", commit.message)
            if merged :
                if not commit.parents :
                    print "WARNING : false merge on %s %s" % ( commit.sha , commit.message )
                else :
                    source = self.new_branch(merged.group('source').strip("'").replace('origin/', ''))
                    branches.append( ( commit.parents[0] , source ) )
                    commit.parents[0].set_branch(source)
                    target = self.new_branch(merged.group('target').strip("'"))
                    branches.append( ( commit.parent , target ) )
                    commit.parent.set_branch(target)

    for sha,branchname in get_branches() :
        branch = self.new_branch(branchname)
        branches.append( ( self[sha] , branch ) )
        self[sha].set_branch( branch )

    n = 0
    for commit in self.values() :
        for c in commit.parents :
            if not c.branch :
                n += 1
                newbranch = self.new_branch("branch_%s" % n)
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
            if c.branch and not branch.is_primary() :
                break
            c.set_branch(branch)
            c = c.parent

    for branch in self.branches.values() :
        branch.sort()

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

    self.order.reverse()
    m = 0
    for c in self.order :
        if not c.branch :
            m += 1
            newbranch = self.new_branch("orphan %s" % m)
            branches.append( ( c , newbranch ) )
            c.set_branch( newbranch )
            c = c.parent
            while c :
                if not c.parent : # Initial commit detection
                    c.set_branch( branch )
                    break
                if c.branch and not branch.is_primary() :
                    break
                c.set_branch(branch)
                c = c.parent
    self.order.reverse()

