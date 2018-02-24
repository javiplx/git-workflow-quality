
var config = {
  elementId:"gitGraph0",
  template:"blackarrow",
  orientation:"horizontal"
};

var gitgraph = new GitGraph(config);

var masterCommit = {dotColor:"blue", dotStrokeColor:"blue"};
var topicCommit = {dotColor:"red", dotStrokeColor:"red"};
var supportCommit = {dotStrokeColor:"darkblue", dotColor:"darkblue"};

var master = gitgraph.branch({name:"master", column:0, color:"blue"});
master.commit(masterCommit);
master.commit(masterCommit);
var support = gitgraph.branch({name:"branch", column:1, color:"darkblue"});
support.commit({dotStrokeColor:"darkblue", dotColor:"darkblue"});
support.commit(supportCommit);
var topic = gitgraph.branch({name:"topic", column:2, color:"red"});
master.commit(masterCommit);
support.commit(supportCommit);
topic.commit(topicCommit);
support.merge(master, {dotStrokeColor:"blue", dotColor:"blue"});
master.commit(masterCommit);
topic.commit({dotColor:"red", dotStrokeColor:"red"});
topic.merge(master, {dotColor:"blue", dotStrokeColor:"blue"});
master.commit(masterCommit);

