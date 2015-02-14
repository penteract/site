function setup(token){
  openChannel(token);
}

function openChannel(token){
  //creates a new channel and checks that it works
  var channel = new goog.appengine.Channel(token);
  var socket = channel.open();
  socket.onmessage = function(m){
    var message=JSON.parse(m.data)
    if(message.request=="NewGame"){
      GameID=message.gameID;
      gname=message.gname
      gpath=message.gpath
      time=message.time
      time=time+" seconds"
      $.post("/respond?answer=wait&gameID="+message.gameID);
      $("#offertext").html(message.player+' has requested a game of '+gname+' with you, the time limit per turn is '+time+'.  do you want to start a game now?')
      $("#offer").show()
      
    }
    else{process(message);}
  };
  socket.onerror = newChannel;
}

function newChannel(){
  $.post('/newchannel',function(data){openChannel(data)})
}
