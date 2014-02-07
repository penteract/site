$.ajaxSetup({cache:false});

function setup(token){
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
      time=message.time
      time=["1 min","2 mins","5 mins","10 mins","1 day","7 days"][time]
      $.post("/respond?answer=wait&gameID="+message.gameID);
      $("body").append('<div id="offer" style="position:fixed;bottom:10px;right:5px;width:20%;min-width:9em">'+message.player+' has requested a game with you, the time limit per turn is '+time+'.  do you want to start a game now?<br><input type="button" onclick= \'$.post("respond", {answer:"yes", gameID:'+message.gameID+'},function(){location.replace("/game?gameID='+message.gameID+'");}); \' value="yes"></input><input type="button" onclick=\'$.post("respond",{answer:"no",gameID:'+message.gameID+'});$("#offer").hide();\' value="no"></input></div>')
    }
    else{process(message);}
  };
  //socket.onopen = function(){clearTimeout(testC);};
  socket.onerror = newChannel;
  /*socket.onclose = onClose;*/
}

function newChannel(){
  $.post('newChannel',function(data){openChannel(data)})
}