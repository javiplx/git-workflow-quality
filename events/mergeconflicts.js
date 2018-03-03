
var config = {
  elementId: "gitGraph5",
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
var topic = gitgraph.branch({name:"topic", column:1, color:"darkblue"});
topic.commit({dotStrokeColor:"darkblue", dotColor:"darkblue"});
topic.commit(topicCommit);
master.checkout();
var master_helper = gitgraph.branch({name:"helper", column:0, color:"red"});
master_helper.commit(supportCommit);
topic.checkout();
var topic_helper = gitgraph.branch({name:"helper", column:1, color:"red"});
master_helper.merge(topic_helper, supportCommit);
topic_helper.merge(master, supportCommit);

