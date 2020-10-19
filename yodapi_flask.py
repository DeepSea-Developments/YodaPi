import sys
import os

import json
import scripts.hotspot_manager as hpm
import configparser
import threading
import time

from base64 import b64encode
from datetime import datetime
from flask import Flask, render_template, Response, request, jsonify, g
from scripts.database import get_db, dictfetchone, init_db, dictfetchall
from scripts.helpers import get_mac, stop_camera_thread, load_config, get_parameters_id_list, DEFAULT_CONFIG_PATH

# from scripts.record_completer import RecordCompleter
# from scripts.camera_thermal import CameraThermal

MAC_ADDRESS = get_mac()

if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    app = Flask(__name__)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/index')
@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


@app.route('/registros')
def registros():
    """Records page."""
    return render_template('records.html')


@app.route('/configuracion')
def configuracion():
    """Settings page."""

    with open('conf/parameters.json') as param_file:
        params = json.load(param_file)

    return render_template('settings.html', params=params)


def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        thermal_image = frame.get('thermal_image')
        # print(frame.get('alert'))
        yield (b'--frame\r\n'
               b'Content-Type: image/png\r\n\r\n' + thermal_image + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(CameraThermal()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/barcode_scan', methods=['POST'])
def barcode_scan():
    content = request.json
    data = content.get('data')

    p_extra_json = data.get('extra_json')
    if p_extra_json is not None:
        p_extra_json = json.dumps(p_extra_json)

    db = get_db()
    cur = db.cursor()
    cur.execute(
        """INSERT INTO records (mac_address, p_barcode_type, p_identification, p_timestamp, p_name, p_last_name, 
        p_gender, p_birth_date, p_blood_type, p_extra_json, p_extra_txt, p_alert) VALUES 
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (MAC_ADDRESS, content.get('barcode_type'), data.get('identification'), content.get('timestamp'),
         data.get('name'), data.get('last_name'), data.get('gender'), data.get('birth_date'), data.get('blood_type'),
         p_extra_json, data.get('extra_txt'), data.get('alert')))
    db.commit()

    RecordCompleter(cur.lastrowid)
    return jsonify(data)


@app.route('/latest_record')
def latest_record():
    now = datetime.now().isoformat()
    cur = get_db().cursor()
    query = """SELECT record_id, p_identification, p_timestamp, p_name, p_last_name, p_gender, p_birth_date, 
    p_blood_type, t_timestamp, t_temperature_p80, t_temperature_body, t_alert, p_alert
    FROM records WHERE(cast(JULIANDAY('{}') - JULIANDAY(t_timestamp)  as float ) *60 * 60 * 24) < {}
    ORDER BY record_id DESC LIMIT 1""".format(now, 5)
    cur.execute(query)
    data = dictfetchone(cur)
    return jsonify(data)


@app.route('/record_thermal')
def record_thermal():
    record_id = request.args.get('record_id', type=int, default=None)
    if record_id is not None:

        cur = get_db().cursor()
        cur.execute("""SELECT record_id, t_image_thermal FROM records WHERE record_id=? LIMIT 1""", (record_id,))
        data = dictfetchone(cur)

        image_thermal = data.get('t_image_thermal')
        if image_thermal is not None:
            data['t_image_thermal'] = b64encode(image_thermal).decode("utf-8")

        return jsonify(data)
    else:
        return None


@app.route('/record_rgb')
def record_rgb():
    record_id = request.args.get('record_id', type=int, default=None)
    if record_id is not None:

        cur = get_db().cursor()
        cur.execute("""SELECT record_id, t_image_rgb FROM records WHERE record_id=? LIMIT 1""", (record_id,))
        data = dictfetchone(cur)

        image_rgb = data.get('t_image_rgb')
        if image_rgb is not None:
            data['t_image_rgb'] = b64encode(image_rgb).decode("utf-8")

        return jsonify(data)
    else:
        return None


@app.route('/records')
def records():
    page_size = request.args.get('page_size', type=int, default=6)
    page = request.args.get('page', type=int, default=1)
    offset = (page - 1) * page_size
    cur = get_db().cursor()

    cur.execute("SELECT COUNT(1) as total FROM records")
    total = dictfetchone(cur)['total']

    num_pages = -(-total // page_size)

    cur.execute("SELECT * FROM records ORDER BY record_id DESC LIMIT ? OFFSET ?", (page_size, offset))
    data = dictfetchall(cur)

    for record in data:
        image_rgb = record.get('t_image_rgb')
        if image_rgb is not None:
            record['t_image_rgb'] = b64encode(image_rgb).decode("utf-8")

    for record in data:
        image_thermal = record.get('t_image_thermal')
        if image_thermal is not None:
            record['t_image_thermal'] = b64encode(image_thermal).decode("utf-8")

    response = {
        'count': total,
        'next': page + 1 if page < num_pages else None,
        'previous': page - 1 if page > 0 else None,
        'results': data
    }

    return jsonify(response)


@app.route('/wifi_status')
def wifi_status():
    ip = hpm.get_wlan0_ip()
    # Conected to HotSpot
    if ip is not None and ip[:7] == "10.0.0.":
        ssid = hpm.get_hostapd_name()
    # Connected to wlan
    else:
        ssid = hpm.get_ssid_name()
    response = {
        'ssid': ssid,
        'ip': ip
    }
    return jsonify(response)


@app.route('/wifi_settings', methods=['POST'])
def wifi_settings():
    data = request.json
    print(data)

    print(hpm.get_networks())
    hpm.set_new_wifi(data['ssid'], data['password'])
    hpm.change_network()
    hpm.reset_autohotspot()

    return jsonify(data)


@app.route('/set_parameters', methods=['POST'])
def set_parameters():
    data = request.json

    # Use a config file
    config = configparser.ConfigParser()
    config.read(DEFAULT_CONFIG_PATH)

    if not ('CUSTOM' in config):
        config.add_section('CUSTOM')

    for key in data:
        config.set('CUSTOM', key, str(data[key]))

    with open(DEFAULT_CONFIG_PATH, 'w') as configfile:
        config.write(configfile)

    return jsonify(data)


@app.route('/get_parameters_default')
def get_parameters_default():
    # Use a config file
    config = configparser.ConfigParser()
    config.read(DEFAULT_CONFIG_PATH)
    conf = config['DEFAULT']

    with open('conf/parameters.json') as param_file:
        params = json.load(param_file)
    param_id_list = get_parameters_id_list(params)
    param_value_list = []
    for id in param_id_list:
        param_value_list.append(conf.get(id))

    data = {}
    for param, value in zip(param_id_list, param_value_list):
        data[param] = value


    # # Default parameters
    # REF_TEMP = conf.get('REF_TEMP')
    # CAM_SENSITIVITY = conf.get('CAM_SENSITIVITY')
    # THRESHOLD_HUMAN_TEMP = conf.get('THRESHOLD_HUMAN_TEMP')
    # ALERT_WARNING_TEMP = conf.get('ALERT_WARNING_TEMP')
    # ALERT_DANGER_TEMP = conf.get('ALERT_DANGER_TEMP')
    # CAPTURE_DELAY = conf.get('CAPTURE_DELAY')
    #
    # data = {
    #     "REF_TEMP": REF_TEMP,
    #     "CAM_SENSITIVITY": CAM_SENSITIVITY,
    #     "THRESHOLD_HUMAN_TEMP": THRESHOLD_HUMAN_TEMP,
    #     "ALERT_WARNING_TEMP": ALERT_WARNING_TEMP,
    #     "ALERT_DANGER_TEMP": ALERT_DANGER_TEMP,
    #     "CAPTURE_DELAY": CAPTURE_DELAY
    # }

    return jsonify(data)


# cfernandez - 01/10/2020
@app.route('/get_parameters_last')
def get_parameters_last():
    # Use a config file
    conf = load_config()

    with open('conf/parameters.json') as param_file:
        params = json.load(param_file)
    param_id_list = get_parameters_id_list(params)
    param_value_list = []
    for id in param_id_list:
        param_value_list.append(conf.get(id))

    data = {}
    for param, value in zip(param_id_list, param_value_list):
        data[param] = value

    # # Default parameters
    # REF_TEMP = conf.get('REF_TEMP')
    # CAM_SENSITIVITY = conf.get('CAM_SENSITIVITY')
    # THRESHOLD_HUMAN_TEMP = conf.get('THRESHOLD_HUMAN_TEMP')
    # ALERT_WARNING_TEMP = conf.get('ALERT_WARNING_TEMP')
    # ALERT_DANGER_TEMP = conf.get('ALERT_DANGER_TEMP')
    # CAPTURE_DELAY = conf.get('CAPTURE_DELAY')
    #
    # data = {
    #     "REF_TEMP": REF_TEMP,
    #     "CAM_SENSITIVITY": CAM_SENSITIVITY,
    #     "THRESHOLD_HUMAN_TEMP": THRESHOLD_HUMAN_TEMP,
    #     "ALERT_WARNING_TEMP": ALERT_WARNING_TEMP,
    #     "ALERT_DANGER_TEMP": ALERT_DANGER_TEMP,
    #     "CAPTURE_DELAY": CAPTURE_DELAY
    # }

    return jsonify(data)


# Main app
def flask_main(port=8080):
    # init_db(app)

    app.run(host='0.0.0.0', port=port, threaded=True)

    # Start camera thread
    # CameraThermal()
