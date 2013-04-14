$.ajaxSetup({cache:false});
//testC="5";
function setup(token){
  testC=setTimeout(newChannel,5000);
  openChannel(token);
}

function openChannel(token){
  //creates a new channel and checks that it works
  var channel = new goog.appengine.Channel(token);
  var socket = channel.open();
  socket.onmessage = function(m){
    var message=JSON.parse(m.data)
    offerGameID=message.gameID;
    //console.log(m.data);
    if(message.request=="NewGame"){
      $.post("/respond?answer=wait&gameID="+message.gameID);
      $("body").append('<div id="offer" style="position:fixed;bottom:10px;right:5px;width:20%;min-width:9em">'+message.player+' has requested a game with you, do you want to start a game now? You have approximately 30 seconds to decide.<br><input type="button" onclick= \'$.post("respond", {answer:"yes", gameID:'+message.gameID+'},function(){location.replace("/game?gameID='+message.gameID+'");}); \' value="yes"></input><input type="button" onclick=\'$.post("respond",{answer:"no",gameID:'+message.gameID+'});$("#offer").hide();\' value="no"></input></div>')
    }
    else{process(message);}
  };
  socket.onopen = function(){clearTimeout(testC);};
  /*socket.onerror = onError;
  socket.onclose = onClose;*/
}

function newChannel(){
  $.post('newChannel',function(data){openChannel(data)})
}