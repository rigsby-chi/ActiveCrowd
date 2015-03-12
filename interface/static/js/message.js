function cleanMessage (selector){
  var messageBlock = selector==null?$('#message'):$(selector);
  messageBlock.empty();
}

function addMessage (type, message, selector){
  var prefix = '';
  if(type=='danger') {prefix = 'Error! '; }
  else if(type=="info") { prefix = 'Info: '; }
  else if(type=='success') { prefix = 'Success. '; }
  else if(type=='warning') { prefix = 'Warning! '; }
  else { return false; }
  
  var messageBlock = selector==null?$('#message'):$(selector);
  
  messageBlock.append('<div class="alert alert-' + type + '" role="alert"><a href="#" class="close" data-dismiss="alert">&times;</a></button><strong>' + prefix + '</strong>' + message + '<i>  (Occur at: ' + new Date().toLocaleString() + ')</i></div>');
}

$(document).ready(function() {
  if( !$('#message').is(':empty')){
    var stream = $('#message').text();
    var message = stream.split(";;;")
    cleanMessage();
    for(var i = 0; i < message.length - 1; i++){
      addMessage(message[i].split(":::")[0], message[i].split(":::")[1]);
    }
  }
});
