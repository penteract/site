function click(pos){
  $.post('makeMove?pos='+pos+'&gameID='+gameID,
  function (data){if (data!="none") alert(data);})
  }

  
function process(m){
  if (m.request=="gameUpdate"){
    if(m.gameID=gameID){
      show(m);
    }
  }
}