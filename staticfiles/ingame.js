

STARTED=4
AIP=2
GAMEOVER=8
DRAW=16
TURN=1
TIMEUP=32

function click(pos){
    $.post('makemove?pos='+pos+'&gameID='+gameID+'&playerID='+playerID,
        function (data){
            if (data[0]!="{") myalert(data)
            else process(JSON.parse(data));})
}

function sendMsg(){
    $.post('msg',{"gameID":gameID,"msg":$("#msg").val()});
    $("#msg").val("");
}


function process(m){
    if (m.request=="gameUpdate" && m.gameID==gameID){
        if (m.message!=lastj.message){
            $("#messages").prepend(m.content+"<br>");
        }
        if((m.state&GAMEOVER)!=(lastj.state&GAMEOVER)){
            myalert("game over: "+m.state&DRAW?"its a draw":
                ((m.state&TURN)==player?"congratulations, you won":"sorry, you lost"))
        }
        $("#"+(m.state&TURN)).addClass("turn")
        $("#"+(1-m.state&TURN)).removeClass("turn")
        
        show(m);
        lastj=m
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
function poller(){
    $.get("getgame",{"gameID":gameID},updatet)
    POLLER=setTimeout(poller,t);t+=1000
}

function updatet(m){
    j=JSON.parse(m)
    if (m!=lastm){t=500;process(j)}
    lastm=m
}

