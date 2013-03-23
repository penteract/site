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
    if(message.request=="NewGame"){
      $.post("/respond?answer=wait&gameID="+message.gameID);
      var offerBox=$("#offer");
      offerBox.html(message.player+' has requested a game with you, click OK to accept, cancel to reject. You have approximately 30 seconds to decide<br><input type="button" onclick= \'$.post("respond", {answer:"yes", gameID:'+message.gameID+'}); location.replace("/game?gameID='+message.gameID+'");\' value="yes"></input><input type="button" onclick=\'$.post("respond",{answer:"no",gameID:'+message.gameID+'});$("#offer").hide();\' value="no"></input>')
      offerBox.show();
    }
    else{process(message);}
  };
  socket.onopen = function(){clearTimeout(testC);};
  /*socket.onerror = onError;
  socket.onclose = onClose;*/
  testC=setTimeout(newChannel,10000);
}

function newChannel(){
  $.post('newChannel',function(data){openChannel(data)})
}