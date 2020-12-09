$(document).ready(function () {
  get_wifi_status()
  setInterval(get_wifi_status, 30 * 1000);
});

function get_wifi_status() {
  $.get("/wifi_status", function (data) {
    if (data) {
      $('#ssid').text(data.ssid)
      $('#ip').text(data.ip)
    }
  });
}