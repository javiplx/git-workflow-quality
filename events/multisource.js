
var config = {
  elementId: "gitGraph3",
  template: "blackarrow",
  orientation: "horizontal"
};

var gitgraph = new GitGraph(config);

var masterCommit = {dotColor:"blue", dotStrokeColor:"blue"};
var topicCommit = {dotColor:"red", dotStrokeColor:"red"};
var supportCommit = {dotStrokeColor:"darkblue", dotColor:"darkblue"};

var master = gitgraph.branch({name:"master", column:0, color:"blue"});
master.commit(masterCommit);
master.commit(masterCommit);
var topic = gitgraph.branch({name:"topic", column:2, color:"red"});
topic.commit({dotStrokeColor:"red", dotColor:"red"});
master.checkout();
master.commit(masterCommit);
var branch = gitgraph.branch({name:"branch", column:1, color:"darkblue"});
branch.commit({dotStrokeColor:"darkblue", dotColor:"darkblue"});
topic.commit(topicCommit);
master.commit(masterCommit);
branch.commit(supportCommit);
branch.merge(topic, {dotColor:"red", dotStrokeColor:"red"});
branch.commit(supportCommit);
master.commit(masterCommit);
topic.commit(topicCommit);

