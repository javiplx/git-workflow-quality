
var config = {
  elementId: "gitGraph1",
  template: "blackarrow",
  orientation: "horizontal"
};

var gitgraph = new GitGraph(config);

var masterCommit = {dotColor:"blue", dotStrokeColor:"blue"};
var offTopicCommit = {dotColor:"red", dotStrokeColor:"red"};
var topicCommit = {dotStrokeColor:"darkblue", dotColor:"darkblue"};

var master = gitgraph.branch({name:"master", column:0, color:"blue"});
master.commit(masterCommit);
master.commit(masterCommit);
var topic = gitgraph.branch({name:"topic", column:1, color:"darkblue"});
topic.commit({dotStrokeColor:"darkblue", dotColor:"darkblue"});
master.commit(masterCommit);
topic.commit(topicCommit);
master.commit(masterCommit);
master.merge(topic, {dotColor:"red", dotStrokeColor:"red"});
master.commit(masterCommit);
topic.commit({dotStrokeColor:"darkblue", dotColor:"darkblue"});

