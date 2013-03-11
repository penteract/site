var channel,socket
var request
var process //function

function setup(token,p){
  process=p;
  openChannel(token);
}

function openChannel(token){
  //creates a new channel and checks that it works
  channel = new goog.appengine.Channel(token);
  socket = channel.open();
  socket.onmessage = function(m){
    message=JSON.parse(m.data)
    if(message.request=="NewGame"){
      //$.post("/respond?answer=wait");
      answer=confirm(message.player+" has requested a game with you, click OK to accept, cancel to reject. You have approximately 30 seconds to decide")
      if (answer) $.post("respond",{answer:"yes",gameID:message.gameID});
      else $.post("respond",{answer:"no",gameID:message.gameID});;
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

/*
function testChannel(){
  $.post('open')
  request=setTimeout(newChannel,1000);
}

function recieve(m){
  if(m.data=="channel is working"){clearTimeout(request);}
  else{process(m)}
}
*/