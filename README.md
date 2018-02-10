
# git workflow quality

This work pretends to stablish a way to get a numeric value for the quality of a git workflow.  
The idea behind is to use elements from graph theory over the repository history/network.

# History

These tools initially started as an attempt to construct a graph representation of the repository
with [gitgraph.js library](http://gitgraphjs.com/). At a very early stage, while constructing the graph
with output from `git log`, the idea about running some graph theory algorithms over it arised.

