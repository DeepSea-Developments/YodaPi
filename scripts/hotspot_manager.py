import re
import os

WPA_SUPPLICANT_FILE = '/etc/wpa_supplicant/wpa_supplicant.conf'


# This works to reset autohotspot. If in hotspot, first search available networks and if not, start hotspot.
def reset_autohotspot():
    sudoPassword = 'raspberry'
    command = '/usr/bin/autohotspot'
    p = os.system('echo %s|sudo -S %s' % (sudoPassword, command))
    print(p)


# This works to change from network to network. NOT from hotspot to network
def change_network():
    sudoPassword = 'raspberry'
    command = 'wpa_cli -i wlan0 reconfigure'
    p = os.system('echo %s|sudo -S %s' % (sudoPassword, command))
    print(p)


# Get available SSID network
def get_networks():
    sudoPassword = 'raspberry'
    command = 'iwlist wlan0 scan|grep SSID'
    p = os.system('echo %s|sudo -S %s' % (sudoPassword, command))
    return p


def set_new_password(password):
    with open(WPA_SUPPLICANT_FILE, 'r') as f:
        in_file = f.read()
        f.close()

    out_file = re.sub(r'psk=".*"', 'psk=' + '"' + password + '"', in_file)

    with open(WPA_SUPPLICANT_FILE, 'w') as f:
        f.write(out_file)
        f.close()


def set_new_wifi(ssid, password):
    with open(WPA_SUPPLICANT_FILE, 'r') as f:
        in_file = f.read()
        f.close()

    psk_file = re.sub(r'psk=".*"', 'psk=' + '"' + password + '"', in_file)
    out_file = re.sub(r'ssid=".*"', 'ssid=' + '"' + ssid + '"', psk_file)

    with open(WPA_SUPPLICANT_FILE, 'w') as f:
        f.write(out_file)
        f.close()


# Get IP of wlan0 interface
def get_wlan0_ip():
    try:
        ipv4 = re.search(re.compile(r'(?<=inet )(.*)(?=\/)', re.M), os.popen('ip addr show wlan0').read()).groups()[0]
        return ipv4
    except:
        print('Could not get wlan0 ip')
        return None


# Get hostapd name
def get_hostapd_name():
    HOSTAPD_FILE = '/etc/hostapd/hostapd.conf'
    f = open(HOSTAPD_FILE, 'r')
    data = f.read()
    f.close()
    return re.search(r'\nssid=(.*)', data).group(1)


# Get SSID name
def get_ssid_name():
    try:
        WPA_SUPPLICANT_FILE = '/etc/wpa_supplicant/wpa_supplicant.conf'
        f = open(WPA_SUPPLICANT_FILE, 'r')
        data = f.read()
        f.close()
        return re.search(r'ssid="(.*)"', data).group(1)
    except:
        print('Could not get ssid name')
        return None
