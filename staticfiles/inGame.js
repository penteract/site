function click(pos){
  $.post('makeMove?pos='+pos+'&gameID='+gameID,
  function (data){if (data!="none") alert(data);})
}

function sendMsg(){
  $.post('msg',{"gameID":gameID,"msg":$("#msg").val()});
  $("#msg").val("");
}

  
function process(m){
  if (m.request=="gameUpdate" && m.gameID==gameID){
    show(m);
  }
  else if(m.request=="gameover" && m.gameID==gameID){
    if(m.reason=="timeup"){alert(m.won?"congratulations, you won":"time up, sorry")}
    else alert(m.won?"congratulations, you won":"sorry, you lost")
  }
  else if(m.request=="message" && m.gameID==gameID){
    $("#messages").prepend(m.content+"<br>");
  }
}

poller=setInterval(function(){
    $.get("getGame",{"gameID":gameID},function(m){show(JSON.parse(m));})
  }, 40000);