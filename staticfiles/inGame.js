function click(pos){
    $.post('makeMove?pos='+pos+'&gameID='+gameID+'&playerID='+playerID,
        function (data){
            if (data[0]!="{") alert(data)
            else show(JSON.parse(data));})
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
        if(m.reason=="timeup"){myalert(m.won?"congratulations, you won":"time up, sorry")}
        else myalert(m.won?"congratulations, you won":"sorry, you lost")
    }
    else if(m.request=="message" && m.gameID==gameID){
        $("#messages").prepend(m.content+"<br>");
    }
}

t=500
lastm=0

function poller(){
    $.get("getGame",{"gameID":gameID},function(m){updatet(JSON.parse(m));})
    setTimeout(poller,t);t+=2000
}

function updatet(j){
	show(j)
	if (j!=lastm){t=500}
    lastm=j
}

