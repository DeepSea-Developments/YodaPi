
$(document).ready(function () {

  //When navbar is active, charge the last parameters
  $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
    var target = $(e.target).attr("href"); //activated tab
    
    if ((target == '#settings-advance')) {
      getParameters_last();
    }
  });

});

function activaTab(tab){
  $('.nav-tabs a[href="#' + tab + '"]').tab('show');
};

function updateWifiSettings() {
  ssid = $('#wifi_ssid').val();
  password = $('#wifi_password').val();
  
  if (ssid && password) {
    const body = {
      ssid: ssid,
      password: password
    };

    $.ajax({
      type: 'POST',
      url: '/wifi_settings',
      data: JSON.stringify(body),
      contentType: 'application/json',
      success: function (response_data) {
        console.log(response_data);
        alert("Reiniciando");
      }
    });
  }
  else {
    alert("Ingresa el SSID y la contraseña de la red.");
  }
}

//cfernandez - 29/09/2020
function updateParameters(){
  //Parametros 
  REF_TEMP = $('#REF_TEMP').val();
  CAM_SENSITIVITY = $('#CAM_SENSITIVITY').val();
  THRESHOLD_HUMAN_TEMP = $('#THRESHOLD_HUMAN_TEMP').val();
  ALERT_WARNING_TEMP = $('#ALERT_WARNING_TEMP').val();
  ALERT_DANGER_TEMP = $('#ALERT_DANGER_TEMP').val();
  CAPTURE_DELAY = $('#CAPTURE_DELAY').val();

  if (REF_TEMP=='' || CAM_SENSITIVITY=='' || THRESHOLD_HUMAN_TEMP=='' || ALERT_WARNING_TEMP=='' || ALERT_DANGER_TEMP=='' || CAPTURE_DELAY==''){
    alert("Ingresa todos los parametros");
    return;
  }

  const data = {
    REF_TEMP: REF_TEMP,
    CAM_SENSITIVITY: CAM_SENSITIVITY,
    THRESHOLD_HUMAN_TEMP: THRESHOLD_HUMAN_TEMP,
    ALERT_WARNING_TEMP: ALERT_WARNING_TEMP,
    ALERT_DANGER_TEMP: ALERT_DANGER_TEMP,
    CAPTURE_DELAY: CAPTURE_DELAY
  };

  $.ajax({
    type: 'POST',
    url: '/camera_parameters',
    data: JSON.stringify(data),
    contentType: 'application/json',
    success: function (response_data) {
      console.log(response_data);
    }
  });

  activaTab('settings-advance');
}

//cfernandez - 29/09/2020
function getParameters_default(){ 
  $.ajax({
    type: 'GET',
    url: '/get_parameters_default',
    success: function (response_data) {
      //Set values 
      $('#REF_TEMP').val(response_data['REF_TEMP']);
      $('#CAM_SENSITIVITY').val(response_data['CAM_SENSITIVITY']);
      $('#THRESHOLD_HUMAN_TEMP').val(response_data['THRESHOLD_HUMAN_TEMP']);
      $('#ALERT_WARNING_TEMP').val(response_data['ALERT_WARNING_TEMP']);
      $('#ALERT_DANGER_TEMP').val(response_data['ALERT_DANGER_TEMP']);
      $('#CAPTURE_DELAY').val(response_data['CAPTURE_DELAY']);
    }
  });
}

//cfernandez - 01/10/2020
function getParameters_last(){ 
  $.ajax({
    type: 'GET',
    url: '/get_parameters_last',
    success: function (response_data) {
      //Set values 
      $('#REF_TEMP').val(response_data['REF_TEMP']);
      $('#CAM_SENSITIVITY').val(response_data['CAM_SENSITIVITY']);
      $('#THRESHOLD_HUMAN_TEMP').val(response_data['THRESHOLD_HUMAN_TEMP']);
      $('#ALERT_WARNING_TEMP').val(response_data['ALERT_WARNING_TEMP']);
      $('#ALERT_DANGER_TEMP').val(response_data['ALERT_DANGER_TEMP']);
      $('#CAPTURE_DELAY').val(response_data['CAPTURE_DELAY']);
    }
  });
}

