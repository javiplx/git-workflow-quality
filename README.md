
# git workflow quality

This work pretends to stablish a way to get a numeric value for the quality of a git workflow.  
The idea behind is to use elements from graph theory over the repository history/network.

# metrics

To get the numerical values we need a few metrics. There are basically two set of metrics, some
which are relevant to the repository as a whole and some others that are applied at the branch
level.

## global metrics

Are calculated from all the available commits, ideally after aggresive garbage collection

- number of commits
- ratio of merge and standard commits
- ammended commits

## branch metrics

The initial metric set is the global one, but we can add some metrics about the relation with other branches

- number of forked branches
- number of different branches merged into (accounting for repetition and _inner_ merges))
- number of branches contributed (merged) to

Merges among branches can generate its own network diagram. The ideal result might have master in the center
and layers around for topic branches, then subtopic branches and so on

### assigning commits to branches

As merged branches are typically removed, we need some heuristics to recover removed branches. We
start with merge commits and travel back following the first parent. The main issue is to decide
which branch a commit _belongs_ to, as their history goes up to the initial commit. Although any
policy enforced about commit messages might improve this assignment, we basically trace the history
of master/develop, and for the remaining commits we just go through parents until a commit assigned
to another branch appears.


## events

There are also some events that we can check, that might be symptom of a defect depending on the
workflow we pretend to use

- <img title="multiple targets" src="https://github.com/javiplx/git-workflow-quality/raw/master/events/multitarget.png" align="top" height=100 /> branches merged on multiple targets
- <img title="reutilized branches" src="https://github.com/javiplx/git-workflow-quality/raw/master/events/reutilized.png" align="top" height=75 /> already merged commits used as branch parent
- <img title="multimerged parent" src="https://github.com/javiplx/git-workflow-quality/raw/master/events/multimerged.png" align="top" height=50 /> source branch merged again in the branch lifetime
- <img title="indirect merges" src="https://github.com/javiplx/git-workflow-quality/raw/master/events/indirect.png" align="top" height=75 /> branches not merged on direct parents
- <img title="multiple sources" src="https://github.com/javiplx/git-workflow-quality/raw/master/events/multisource.png" align="top" height=75 /> branches with multiple contributors

# History

These tools initially started as an attempt to construct a graph representation of the repository
with [gitgraph.js library](http://gitgraphjs.com/). At a very early stage, while constructing the graph
with output from `git log`, the idea about running some graph theory algorithms over it arised.

