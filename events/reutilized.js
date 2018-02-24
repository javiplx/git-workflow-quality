
var config = {
  elementId: "gitGraph2",
  template: "blackarrow",
  orientation: "horizontal"
};

var gitgraph = new GitGraph(config);

var masterCommit = {dotColor:"blue", dotStrokeColor:"blue"};
var topicCommit = {dotColor:"darkblue", dotStrokeColor:"darkblue"};
var supportCommit = {dotStrokeColor:"darkblue", dotColor:"darkblue"};

var master = gitgraph.branch({name:"master", column:0, color:"blue"});
var support = gitgraph.branch({name:"branch", column:1, color:"darkblue"});
master.commit(masterCommit);
support.commit(supportCommit);
support.commit(supportCommit);
var topic = gitgraph.branch({name:"topic", column:1, color:"red"});
support.merge(master, {dotColor:"blue", dotStrokeColor:"blue"});
topic.commit({dotStrokeColor:"red", dotColor:"red"});
master.commit(masterCommit);

