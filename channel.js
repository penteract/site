var channel,socket
var request

function setup(token){
  $("#offer").hide();
  openChannel(token);
}

function openChannel(token){
  //creates a new channel and checks that it works
  var channel = new goog.appengine.Channel(token);
  var socket = channel.open();
  socket.onmessage = function(m){
    var message=JSON.parse(m.data)
    offerGameID=message.gameID;
    console.log(m.data);
    if(message.request=="NewGame"){
      $.post("/respond?answer=wait&gameID="+message.gameID);
      offerBox=$("#offer");
      offerBox.html(message.player+' has requested a game with you, click OK to accept, cancel to reject. You have approximately 30 seconds to decide<br><input type="button" onclick= \'$.post("respond", {answer:"yes", gameID:offerGameID}); $("#offer").hide();\' value="yes"></input><input type="button" onclick=\'$.post("respond",{answer:"no",gameID:offerGameID});$("#offer").hide();\' value="no"></input>')
      offerBox.show();
    }
    else{process(message);}
  };
  socket.onopen = function(){clearTimeout(testC);};
  /*socket.onerror = onError;
  socket.onclose = onClose;*/
  testC=setTimeout(newChannel,1000);
}

function newChannel(){
  $.post('newChannel',function(data){openChannel(data)})
}