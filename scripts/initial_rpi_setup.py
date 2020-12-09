import re
from getmac import get_mac_address

HOSTAPD_FILE = '/etc/hostapd/hostapd.conf'


def set_hostapd(ssid, password):
    mac = get_mac_address()
    format_mac = re.sub(':', '-', mac)
    short_mac = format_mac[-6:]
    with open(HOSTAPD_FILE, 'r') as f:
        in_file = f.read()
        f.close()
    psk_file = re.sub(r'\nwpa_passphrase=.*', '\nwpa_passphrase=' + password, in_file)
    out_file = re.sub(r'\nssid=.*', '\nssid=' + ssid + short_mac, psk_file)

    with open(HOSTAPD_FILE, 'w') as f:
        f.write(out_file)
        f.close()


set_hostapd("TermoDeep", "thermalsmile")
