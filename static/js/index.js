//Global variables
var id_current_record;
var has_thermal = false;
var has_rgb = false;


$(document).ready(function () {
  console.log('stream');
  setInterval(getLatestRecord, 1000);
});


function formateDateTime(m) {
  var hours = m.getHours();
  var ampm = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12;
  hours = hours ? hours : 12;

  return m.getFullYear() + "-" +
    ("0" + (m.getMonth() + 1)).slice(-2) + "-" +
    ("0" + m.getDate()).slice(-2) + " " +
    hours + ":" +
    ("0" + m.getMinutes()).slice(-2) + ":" +
    ("0" + m.getSeconds()).slice(-2) + ' ' +
    ampm;
}

function getLatestRecord() {
  $.get("/latest_record", function (data) {
    if (data) {
      if (data.p_name) {
        $('#name').text(data.p_name + ' ' + data.p_last_name);
        $('#lbl_name').show();
        $('#name').show();
      }
      else {
        $('#lbl_name').hide();
        $('#name').hide();
      }

      if (data.p_identification) {
        $('#identification').text(data.p_identification);
        $('#lbl_identification').show();
        $('#identification').show();
      }
      else {
        $('#lbl_identification').hide();
        $('#identification').hide();
      }

      if (data.p_gender) {
        $('#gender').text(data.p_gender);
        $('#lbl_gender').show();
        $('#gender').show();
      }
      else {
        $('#lbl_gender').hide();
        $('#gender').hide();
      }

      if (data.p_timestamp) {
        timestamp = new Date(data.p_timestamp);
        $('#timestamp').text(formateDateTime(timestamp));
        $('#lbl_timestamp').show();
        $('#timestamp').show();
      }
      else {
        $('#lbl_timestamp').hide();
        $('#timestamp').hide();
      }

      if (data.p_birth_date) {
        $('#birth_date').text(data.p_birth_date);
        $('#lbl_birth_date').show();
        $('#birth_date').show();
      }
      else {
        $('#lbl_birth_date').hide();
        $('#birth_date').hide();
      }

      if (data.p_nationality) {
        $('#nationality').text(data.p_nationality);
        $('#lbl_nationality').show();
        $('#nationality').show();
      }
      else {
        $('#lbl_nationality').hide();
        $('#nationality').hide();
      }

      if (data.p_document_type) {
        $('#document_type').text(data.p_document_type);
        $('#lbl_document_type').show();
        $('#document_type').show();
      }
      else {
        $('#lbl_document_type').hide();
        $('#document_type').hide();
      }

      $('#temperature_body').text(data.t_temperature_body);
      $('#temperature_skin').text(data.t_temperature_p80);
      $('#temperature_body').show()
      $('#temperature_skin').hide()
      $('#lbl_temperature_skin').hide()

      if (data.t_alert == 0) {
        $('#alert_0').show();
        $('#alert_1').hide();
        $('#alert_2').hide();
      }
      else if (data.t_alert == 1) {
        $('#alert_0').hide();
        $('#alert_1').show();
        $('#alert_2').hide();
      }
      else if (data.t_alert == 2) {
        $('#alert_0').hide();
        $('#alert_1').hide();
        $('#alert_2').show();
      }
      else {
        $('#alert_0').hide();
        $('#alert_1').hide();
        $('#alert_2').hide();
      }

      if (data.p_alert == 1) {
        $('#alert_p').show();
      }
      else {
        $('#alert_p').hide();
      }

      if (id_current_record == data.record_id) {
        if (!has_rgb) {
          getRecordRGBImage(id_current_record);
        }
        if (!has_thermal) {
          getRecordThermalImage(id_current_record);
        }
      }
      else {
        id_current_record = data.record_id;
        getRecordRGBImage(id_current_record);
        getRecordThermalImage(id_current_record);
      }
    }
    else {
      $('#name').hide();
      $('#identification').hide();
      $('#gender').hide();
      $('#timestamp').hide();
      $('#birth_date').hide();
      $('#nationality').hide();
      $('#document_type').hide();
      $('#alert_0').hide();
      $('#alert_1').hide();
      $('#alert_2').hide();
      $('#alert_p').hide();
      $('#image_thermal').hide();
      $('#image_rgb').hide();
      $('#temperature_body').hide()
      $('#temperature_skin').hide()
    }
  });
}

function getRecordThermalImage(record_id) {
  $.get("/record_thermal", { record_id: record_id }, function (data) {
    if (data) {
      if (data.t_image_thermal) {
        has_thermal = true;
        $('#image_thermal').show();
        $("#image_thermal").attr("src", 'data:image/png;base64, ' + data.t_image_thermal);
      }
      else {
        has_thermal = false;
        $('#image_thermal').hide();
      }
    }
  });
}

function getRecordRGBImage(record_id) {
  $.get("/record_rgb", { record_id: record_id }, function (data) {
    if (data) {
      if (data.t_image_rgb) {
        has_rgb = true;
        $('#image_rgb').show();
        $("#image_rgb").attr("src", 'data:image/jpeg;base64, ' + data.t_image_rgb);
      }
      else {
        has_rgb = false;
        $('#image_rgb').hide();
      }
    }
  });
}
