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

import dbus
import web
from web import form
from util import get_offlinemode_status, set_offlinemode_status, \
    set_technology_status, add_technology_links

wifi = "ON"
bluetooth = "ON"

form = web.form.Form(
    web.form.Radio('wifi', args=["ON", "OFF"],
                   value=wifi,
                   description="Wifi"),
    web.form.Radio('bluetooth', args=["ON", "OFF"],
                   value=bluetooth,
                   description="Bluetooth"),
    web.form.Button('Submit', value="technology"))


def view():
    rendered = form.render()
    return add_technology_links(rendered,
                                form.get("bluetooth").value)


def update(input):
    if input.wifi != wifi:
        set_technology_status("wifi", input.wifi)

    if input.bluetooth != bluetooth:
        set_technology_status("bluetooth", input.bluetooth)
