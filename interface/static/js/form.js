//Append label class
$(function () {
  $('form .row label').not('#execution label').addClass('col-sm-3');
  $('form .row input, form .row button').not('.input-group input').not('input[type="number"]').not('#execution input').addClass('col-sm-8');
  $('#execution label').addClass('col-sm-5');
  $('#execution input').addClass('col-sm-7');
  $('#execution div.inputField').css('padding-left', '0px');
  $('form .row .block').addClass('col-sm-8');
  $('form .row textarea').addClass('col-sm-8');
  $('form div.required label').prepend('<span style="color: red;">*</span>');
});

//Append prev/next button
$(document).ready(function() {
  if($('fieldset').length > 1){
    $('fieldset').slice(1).hide();
    $('fieldset').slice().append('<br>')
    $('fieldset:first').not("#execution fieldset").append('<div class="action"><button type="button" name="prev" class="btn btn-default" style="visibility: hidden"><span class="glyphicon glyphicon-chevron-left"></span> Prev</button><button type="button" name="next" class="btn btn-default">Next <span class="glyphicon glyphicon-chevron-right"></span></button></div>');
    
    $('fieldset').slice(1, $('.fieldset').length -1).append('<div class="action"><button type="button" name="prev" class="btn btn-default"><span class="glyphicon glyphicon-chevron-left"></span> Prev</button><button type="button" name="next" class="btn btn-default">Next <span class="glyphicon glyphicon-chevron-right"></span></button></div>');
    
    $('fieldset:last').not("#execution fieldset").append('<div class="action"><button type="button" name="prev" class="btn btn-default"><span class="glyphicon glyphicon-chevron-left"></span> Prev</button><button type="submit" name="save" class="btn btn-default">Save <span class="glyphicon glyphicon-save"></span></button></div>');
  }
  else{
    $('fieldset:last').not("#execution fieldset").append('<div class="action"><button type="submit" name="save" class="btn btn-default">Save <span class="glyphicon glyphicon-save"></span></button></div>');
  }
});

var currentpart = 1;
var goNext = true;


$("body").on('click', '.action > button[name="save"], #execution button[name="execute"]', function(e) {
  goNext = true;
  //for sklearn setting checking
  var additionClass = '';
  if($('#classifierClass').length){
    additionClass = '.' + $('#classifierClass').val();
  }
  if( !checkNonEmpty(additionClass) ){
    e.preventDefault();
    return false;
  }
});

$("body").on('click', '.action > button[name="next"]', function(e) {
  $(window).scrollTop(0);
  goNext = true;
  checkNonEmpty ();
  if(goNext == true){
    for(var i = 1; i <= 3; i++){
      $("#part" + i).hide();
    }
    currentpart ++;
    $("#part" + currentpart).show();
  }
});

$("body").on('click', '.action > button[name="prev"]', function(e) {
  for(var i = 1; i <= 3; i++){
    $("#part" + i).hide();
  }
  currentpart --;
  $("#part" + currentpart).show();
  $(window).scrollTop(0);
});

$(document).on('change', '.btn-file :file', function() {
  var input = $(this),
      numFiles = input.get(0).files ? input.get(0).files.length : 1,
      label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
  input.trigger('fileselect', [numFiles, label]);
});

$(document).ready( function() {
  $('.btn-file :file').on('fileselect', function(event, numFiles, label) {
    var input = $(this).parents('.input-group').find(':text'),
        log = numFiles > 1 ? numFiles + ' files selected' : label;
    
    if( input.length ) {
        input.val(log);
    } else {
        if( log ) alert(log);
    }
  });
});

function checkNonEmpty(additionClass){
  if(additionClass == null)
    additionClass = '';
  $('#part' + currentpart + ' div.required' + additionClass + ' input').not('div.hidden input').each( function (){
    if(!$(this).val()){
      goNext = false;
      $(this).closest('div.required').addClass('has-error');
    } 
    else {
      $(this).closest('div.required').removeClass('has-error');
    }
  });
  $('#part' + currentpart + ' div.required' + additionClass + ' textarea').not('div.hidden textarea').each( function (){
    if(!$(this).val()){
      goNext = false;
      $(this).closest('div.required').addClass('has-error');
    } 
    else {
      $(this).closest('div.required').removeClass('has-error');
    }
  });
  
  if(goNext == false){
    addMessage('danger', 'Block(s) in red must not be empty.');
    return false;
  }
  return true;
}

function displayOption(element){
  $(element).closest('fieldset').children('.option').hide();
  $(element).closest('fieldset').children('.option').addClass('hidden');
  $(element).closest('fieldset').children('.' + $(element).val()).show();
  $(element).closest('fieldset').children('.' + $(element).val()).removeClass('hidden');
}

$("body").on('click', '.displayOption', function(e) {
  displayOption(this);
});

$(document).ready(function() {
  var displaySet = $('.displayOption')
  for(var i = 0; i < displaySet.length; i++){
    if($(displaySet[i]).is(":checked")) {
      displayOption(displaySet[i]);
    }
  }
});

function disableAllFields(){
  $('input').prop('disabled', true);
  $('textarea').prop('disabled', true);
  $('button').not('button[name="next"], button[name="prev"]').prop('disabled', true);
  $('select').prop('disabled', true);
  $('.selectpicker').selectpicker('refresh');
}
