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
import re
import shutil
import crypt, uuid
from subprocess import call


bus = dbus.SystemBus()
# just get the services once.  Need to update as new services come in, or after a forced scan
manager = dbus.Interface(bus.get_object("net.connman", "/"), "net.connman.Manager")
manager_services = {}

def update_manager_services():
	global manager_services
	global manager
	manager_services = manager.GetServices()

def get_allowed_users(filename):
	try:
		with open(filename) as f:
			content = f.readlines()
	except:
		return []

	f.close()

	users = []
	for line in content:
		if line.startswith("#"):
			next
		splitted = line.rstrip('\n').split(" ", 1)
		try:
			users.append((splitted[0], splitted[1]))
		except:
			return []
	return users

def set_root_password(new_password):
	filename = "/etc/shadow"
	orig = filename + ".orig"
	new = filename + ".new"

	try:
		with open(filename) as f:
			content = f.readlines()
	except:
		return "Cannot open %s" % filename

	f.close()

	try:
		f = open(new, "w")
	except:
		return "Cannot open %s" % new

		salt = "$6$" + uuid.uuid4().hex + "$"
		new_hashed_password = crypt.crypt(new_password, salt)

	for line in content:
		splitted = line.rstrip('\n').split(":", 2)
		if splitted[0] == "root":
			try:
				f.write("root:" + new_hashed_password + ":" + splitted[2] + "\n")
			except IOError, err:
				f.close()
				return "Cannot write password for the root user, %s" % err
		else:
			f.write(line)
	f.close()

	try:
		shutil.move(filename, orig)
	except:
		return "Cannot move %s to %s" % (filename, orig)

	try:
		shutil.move(new, filename)
	except:
		return "Cannot move %s to %s" % (new, filename)

	try:
		shutil.copymode(orig, filename)
	except:
		return "Cannot set permissions of %s" % filename

	return ""

def extract_values(values):
	val = "{"
	for key in values.keys():
		val += " " + key + "="
		if key in ["PrefixLength"]:
			val += "%s" % (int(values[key]))
		else:
			if key in ["Servers", "Excludes"]:
				val += extract_list(values[key])
			else:
				val += str(values[key])
	val += " }"
	return val

def extract_list(list):
	val = "["
	for i in list:
		val += " " + str(i)
	val += " ]"
	return val


def get_value(properties, key):
        if key in ["IPv4", "IPv4.Configuration",
                   "IPv6", "IPv6.Configuration",
                   "Proxy", "Proxy.Configuration",
                   "Ethernet", "Provider"]:
            val = extract_values(properties[key])
        elif key in ["Nameservers", "Nameservers.Configuration",
                     "Domains", "Domains.Configuration",
                     "Timeservers", "Timeservers.Configuration",
                     "Security"]:
            val = extract_list(properties[key])
        elif key in ["Favorite", "Immutable", "AutoConnect",
                     "LoginRequired", "PassphraseRequired"]:
            if properties[key] == dbus.Boolean(1):
                val = "true"
            else:
                val = "false"
        elif key in ["Strength"]:
            val = int(properties[key])
        else:
            try:
		    val = properties[key]
	    except:
		    val = "<unknown>"
        return val

def get_str_value(properties, key):
	value = get_value(properties, key)
	if value == "<unknown>":
		return ""
	else:
		return str(value).translate(None, "[]{}").strip()

def get_raw_value(properties, key):
	try:
		val = properties[key]
	except:
		val = None
	return val

def get_dict_value(properties, key, value):
    try:
        return str(get_raw_value(properties, key)[value])
    except:
        return ""

def get_service(service_id):
	# bus = dbus.SystemBus()
	path = "/net/connman/service/" + service_id
	service = dbus.Interface(bus.get_object("net.connman", path),
				 "net.connman.Service")
	return service

def get_services():
	# bus = dbus.SystemBus()
	# manager = dbus.Interface(bus.get_object("net.connman", "/"),
	# 			 "net.connman.Manager")
	# return manager.GetServices()
	return manager_services

def get_properties(service_id):
	service = get_service(service_id)
	try:
		return service.GetProperties()
	except:
		return {}

def get_technology_properties():
	# bus = dbus.SystemBus()
	# manager = dbus.Interface(bus.get_object("net.connman", "/"),
	# 				"net.connman.Manager")
        return manager.GetTechnologies()

def get_offlinemode_status():
	# bus = dbus.SystemBus()
	# manager = dbus.Interface(bus.get_object("net.connman", "/"),
	# 				"net.connman.Manager")
	return manager.GetProperties()["OfflineMode"]

def set_offlinemode_status(new_mode):
	# bus = dbus.SystemBus()
	# manager = dbus.Interface(bus.get_object("net.connman", "/"),
	# 				"net.connman.Manager")
	return manager.SetProperty("OfflineMode", new_mode)

def get_tethering_status(technology_type):
	tech_path = "/net/connman/technology/" + technology_type
	for path, properties in get_technology_properties():
		if path == tech_path:
			try:
				if properties["Tethering"] == dbus.Boolean(True):
					status = "ON"
				else:
					status = "OFF"

				if technology_type == "wifi":
					return (status,
						properties["TetheringIdentifier"],
						properties["TetheringPassphrase"])
				else:
					return status
			except KeyError, error:
				return ("OFF", "", "")

	if technology_type == "wifi":
		return (None, "", "")
	return None

def bluetooth_enable_ssp(adapter):
	call(["hciconfig", adapter, "sspmode", "1"])

def bluetooth_disable_ssp(adapter):
	call(["hciconfig", adapter, "sspmode", "0"])

def bluetooth_set_pairable(value):
	if value:
		call(["bluetoothctl", "pairable", "on"])
	else:
		call(["bluetoothctl", "pairable", "off"])

def set_bt_discoverable(value):
	bus = dbus.SystemBus()
	manager = dbus.Interface(bus.get_object("org.bluez", "/"),
				"org.freedesktop.DBus.ObjectManager")
	objects = manager.GetManagedObjects()
	for path, interfaces in objects.iteritems():
		if "org.bluez.Adapter1" not in interfaces.keys():
			continue

		adapter = dbus.Interface(bus.get_object("org.bluez",
							path),
					 "org.freedesktop.DBus.Properties")
		try:
			adapter.Set("org.bluez.Adapter1", "Discoverable",
				    dbus.Boolean(value))
		except dbus.DBusException, error:
			return error
	return None

def set_tethering_status(technology_type, new_status, ssid = None,
			 passphrase = None):
	path = "/net/connman/technology/" + technology_type
	bus = dbus.SystemBus()
	technology = dbus.Interface(bus.get_object("net.connman", path),
					"net.connman.Technology")
	if new_status != None:
		if new_status == "ON":
			mode = dbus.Boolean(True)
		else:
			mode = dbus.Boolean(False)

	if technology_type == "wifi":
		if ssid != None:
			try:
				technology.SetProperty("TetheringIdentifier", ssid)
			except:
				pass
		if passphrase != None:
			try:
				technology.SetProperty("TetheringPassphrase", passphrase)
			except:
				pass

	if new_status != None:
		try:
			technology.SetProperty("Tethering", mode)
		except:
			pass


def get_technology_status(technology_type=None):
	if technology_type != None:
		tech_path = "/net/connman/technology/" + technology_type
	else:
		wifi_path = "/net/connman/technology/wifi"
		bluetooth_path = "/net/connman/technology/bluetooth"
		tech_path = ""
		status_wired = status_wifi = status_cellular = \
		    status_bluetooth = status_gadget = "OFF"
	for path, properties in get_technology_properties():
		if path == tech_path:
			if properties["Powered"] == dbus.Boolean(True):
				status = "ON"
			else:
				status = "OFF"
			return status
		else:
			if path == wifi_path:
				if properties["Powered"] == dbus.Boolean(True):
					status_wifi = "ON"
				else:
					status_wifi = "OFF"
			elif path == bluetooth_path:
				if properties["Powered"] == dbus.Boolean(True):
					status_bluetooth = "ON"
				else:
					status_bluetooth = "OFF"

	return (status_wifi, status_bluetooth)

def set_technology_status(technology_type, new_status):
	path = "/net/connman/technology/" + technology_type
	bus = dbus.SystemBus()
	technology = dbus.Interface(bus.get_object("net.connman", path),
					"net.connman.Technology")
	if new_status == "ON":
		mode = dbus.Boolean(True)
	else:
		mode = dbus.Boolean(False)

	try:
		technology.SetProperty("Powered", mode)
	except:
		pass

def split_lines(lines):
	return iter(lines.splitlines())

def restyle(content):
	# add id field to <tr> so that we can disable rows if necessary
	i = 0
	lines = list(split_lines(content))
	for line in lines:
		id = re.search("label for=\"(.+?)\"\>", line)
		if id == None:
			id_str = "no"
		else:
			id_str = line[id.start()+11:id.end()-2]
		lines[i] = line.replace("<tr>",
					"<tr id=\"" + id_str + "-id\">")
		i = i + 1
	return "\n".join(lines)

def add_technology_links(content, bt):
	# add link to label field so that we can edit the tech if necessary
	i = 0
	lines = list(split_lines(content))
	for line in lines:
		reg = re.search("<tr><th><label for=\"(.+)?\"\>(.+)?\<\/label\>(.*)", line)
		if reg != None:
			tech = reg.group(1)
			if tech == "bluetooth" and bt == "ON":
				name = reg.group(2)
				rest = reg.group(3)
				lines[i] = "<tr><th><label for=\"" + tech + \
				    "\"><a href=\"/" + tech + "\">" + \
				    name + "</a></label>" + rest
				i = i + 1
				continue
		lines[i] = line
		i = i + 1
	return "\n".join(lines)

def request_rescan(technology_type):
	path = "/net/connman/technology/" + technology_type
	bus = dbus.SystemBus()
	try:
		technology = dbus.Interface(bus.get_object("net.connman", path),
					    "net.connman.Technology")
		technology.Scan()

	except:
		return
	# update the services after a scan
	finally:
		update_manager_services()

def is_known_service(service_id):
	properties = get_properties(service_id)
	if len(properties) == 0:
		return False
	favorite = get_raw_value(properties, "Favorite")
	if favorite == None:
		return False
	else:
		return favorite

def is_vpn_service(service_id):
	properties = get_properties(service_id)
	if len(properties) == 0:
		return False
	return get_value(properties, "Type") == "vpn"

def is_cellular_service(service_id):
	properties = get_properties(service_id)
	if len(properties) == 0:
		return False
	return get_value(properties, "Type") == "cellular"

def is_immutable_service(service_id):
	properties = get_properties(service_id)
	if len(properties) == 0:
		return False
	return get_value(properties, "Immutable") == "true"

def get_security(service_id):
	properties = get_properties(service_id)
	if len(properties) == 0:
		return []
	return get_value(properties, "Security")

def get_bt_devices():
	return []

def get_service_type(service_id):
	properties = get_properties(service_id)
	if len(properties) == 0:
		return ""
	return get_value(properties, "Type")

def change_cellular_pin(oldpin, newpin, path = None):
	bus = dbus.SystemBus()
	try:
		manager = dbus.Interface(bus.get_object('org.ofono', '/'),
					 'org.ofono.Manager')
		modems = manager.GetModems()
		if path == None:
			path = modems[0][0]

		simmanager = dbus.Interface(bus.get_object('org.ofono', path),
					    'org.ofono.SimManager')
		simmanager.ChangePin("pin", oldpin, newpin)
		return path
	except dbus.DBusException, error:
		return None

def set_cellular_pin(newpin, path = None):
	bus = dbus.SystemBus()
	try:
		manager = dbus.Interface(bus.get_object('org.ofono', '/'),
					 'org.ofono.Manager')
		modems = manager.GetModems()
		if path == None:
			path = modems[0][0]

		simmanager = dbus.Interface(bus.get_object('org.ofono', path),
					    'org.ofono.SimManager')
		simmanager.EnterPin("pin", newpin)
		return (None, path)
	except dbus.DBusException, error:
		return (error, None)

def activate_cellular(context = None):
	bus = dbus.SystemBus()
	manager = dbus.Interface(bus.get_object('org.ofono', '/'),
				 'org.ofono.Manager')
	modems = manager.GetModems()
	for path, properties in modems:
		if "org.ofono.ConnectionManager" not in properties["Interfaces"]:
			continue

		connman = dbus.Interface(bus.get_object('org.ofono', path),
					 'org.ofono.ConnectionManager')
		try:
			contexts = connman.GetContexts()
		except dbus.DBusException, error:
			return (error, "Cannot get context.")

		if (len(contexts) == 0):
			return (None, "No context available")

		connman.SetProperty("Powered", dbus.Boolean(1))

		if context != None:
			path = context
		else:
			path = contexts[0][0]

		context = dbus.Interface(bus.get_object('org.ofono', path),
					 'org.ofono.ConnectionContext')
		try:
			context.SetProperty("Active", dbus.Boolean(1),
					    timeout = 100)
			return (None, None)
		except dbus.DBusException, e:
			return (e, None)

	return (None, "No context found")
