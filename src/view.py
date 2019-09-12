#
# ECA web UI
#
# Copyright (C) 2013  Intel Corporation. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import web
import config
import dbus
from eca import render, title, help
from util import get_value, get_properties, get_tethering_status, \
    get_offlinemode_status, get_technology_status, get_services, update_manager_services
import technology
import tethering
import rescan

first_load = True

def listing(**k):
    return render.listing(get_services())


def main_screen():
    (tethering.wifi, tethering.ssid,
     tethering.passphrase) = get_tethering_status("wifi")
    tethering.bluetooth = get_tethering_status("bluetooth")

    if tethering.wifi is None:
        tethering.wifi = "OFF"

    if tethering.bluetooth is None:
        tethering.bluetooth = "OFF"

    tethering.form.get('ssid').value = tethering.ssid
    tethering.form.get('passphrase').value = tethering.passphrase
    tethering.form.get('wifi').value = tethering.wifi
    tethering.form.get('bluetooth').value = tethering.bluetooth

    (technology.wifi, technology.bluetooth) = get_technology_status()
    technology.form.get('wifi').value = technology.wifi
    technology.form.get('bluetooth').value = technology.bluetooth

    # don't want to update manager services on first load to reduce time to bring up page
    global first_load
    if first_load:
        first_load = False
    else:
        update_manager_services()

    return render.base(listing(),
                       title, help)
