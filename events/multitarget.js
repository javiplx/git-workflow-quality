
var config = {
  elementId: "gitGraph4",
  template: "blackarrow",
  orientation: "horizontal"
};

var gitgraph = new GitGraph(config);

var masterCommit = {dotColor:"blue", dotStrokeColor:"blue"};
var topicCommit = {dotColor:"darkblue", dotStrokeColor:"darkblue"};
var supportCommit = {dotStrokeColor:"red", dotColor:"red"};

var master = gitgraph.branch({name:"master", column:0, color:"blue"});
master.commit(masterCommit);
master.commit(masterCommit);
var topic0 = gitgraph.branch({name:"topic", column:3, color:"darkblue"});
topic0.commit({dotStrokeColor:"darkblue", dotColor:"darkblue"});
master.checkout();
master.commit(masterCommit);
var topic = gitgraph.branch({name:"topic", column:2, color:"darkblue"});
topic.commit({dotStrokeColor:"darkblue", dotColor:"darkblue"});
master.checkout();
master.commit(masterCommit);
var branch = gitgraph.branch({name:"branch", column:1, color:"red"});
branch.commit({dotStrokeColor:"red", dotColor:"red"});
topic0.commit(topicCommit);
master.commit(masterCommit);
branch.commit(supportCommit);
branch.merge(topic, {dotColor:"darkblue", dotStrokeColor:"darkblue"});
master.commit(masterCommit);
topic.commit(topicCommit);
branch.commit(supportCommit);
branch.merge(topic0, {dotColor:"darkblue", dotStrokeColor:"darkblue"});
branch.commit(supportCommit);
topic.commit(topicCommit);
topic0.commit(topicCommit);
branch.merge(master, {dotColor:"blue", dotStrokeColor:"blue"});
master.commit(masterCommit);

