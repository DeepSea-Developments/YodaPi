$(document).ready(function () {
  getRecords(1);
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

function getRecords(page) {
  page_size = 4;
  $.get("/records", { page: page, page_size: page_size }, function (data) {
    if (data && data.results) {
      var tbl_body = "";
      data.results.forEach(record => {
        var tbl_row = "";
        tbl_row += "<td class='sub-title'>" + (record.p_timestamp ? formateDateTime(new Date(record.p_timestamp)) : '') + "</td>";
        tbl_row += "<td class='sub-title'>" + (record.p_identification ? record.p_identification : '') + "</td>";
        tbl_row += "<td class='sub-title'>" + (record.p_name ? record.p_name : '') + "</td>";
        tbl_row += "<td class='sub-title'>" + (record.p_last_name ? record.p_last_name : '') + "</td>";
        tbl_row += "<td class='sub-title'>" + (record.t_temperature_body ? record.t_temperature_body : '') + "</td>";

        alert_html = ""
        if (record.t_alert == 0) {
          alert_html = "<button type='button' class='btn btn-success alert_button_records'>Permitido</button>";
        }
        else if (record.t_alert == 1) {
          alert_html = "<button type='button' class='btn btn-warning alert_button_records'>Advertencia</button>";
        }
        else if (record.t_alert == 2) {
          alert_html = "<button type='button' class='btn btn-danger alert_button_records'>Peligro</button>";
        }
        tbl_row += "<td class='sub-title'>" + alert_html + "</td>";
        tbl_row += "<td>" + (record.t_image_thermal ? "<img src='data:image/png;base64, " + record.t_image_thermal + "' width=200>" : '') + "</td>";
        tbl_row += "<td>" + (record.t_image_rgb ? "<img src='data:image/png;base64, " + record.t_image_rgb + "' width=200>" : '') + "</td>";
        tbl_body += "<tr>" + tbl_row + "</tr>";
      });
      $("#table-register").html(tbl_body);

      var pagination_body = "";
      number_pages = Math.ceil(data.count / page_size);
      pagination_body += '<li class="page-item"><a class="page-link" href="javascript:void(0)" onclick="getRecords(' + 1 + ');">Primera</a></li>';

      var radius = 3;
      var max_min = number_pages - 2 * radius;
      var min = (page - radius) > 0 ? ((page - radius) <= max_min ? (page - radius) : max_min) : 1;
      var max = (min + 2 * radius) <= number_pages ? (min + 2 * radius) : number_pages;
      for (i = min; i <= max; i++) {
        pagination_body += '<li class="page-item' + (page == i ? ' active' : '') + '"><a class="page-link test" href="javascript:void(0)" onclick="getRecords(' + i + ');">' + i + '</a></li>';
      }
      pagination_body += '<li class="page-item"><a class="page-link" href="javascript:void(0)" onclick="getRecords(' + number_pages + ');">Última</a></li>';

      $("#records_pagination").html(pagination_body);
    }
  });
}
