

function setup(token){
  openChannel(token);
}

function openChannel(token){
  //creates a new channel and checks that it works
  var channel = new goog.appengine.Channel(token);
  var socket = channel.open();
  socket.onmessage = function(m){
    var message=JSON.parse(m.data)
    console.log(message)
    offerGameID=message.gameID;
    if(message.request=="NewGame"){
      time=message.time
      time=["1 min","2 mins","5 mins","10 mins","1 day","7 days"][time]
      $.post("/respond?answer=wait&gameID="+message.gameID);
      $("#offertext").html(message.player+' has requested a game with you,'+
                           ' the time limit per turn is '+time+'.'+
                           ' Do you want to start a game now?')
      $("#offer").show()
      console.log("req recieved")
      
    }
    else{process(message);}
  };
  socket.onerror = newChannel;
}

function newChannel(){
  $.post('newChannel',function(data){openChannel(data)})
}
