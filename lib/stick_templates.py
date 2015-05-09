import stick_const
import os

#def generate_vm(resolvers, nic_tag, ip, gateway, netmask, ssh_key):
# def generate_vm(alias, resolvers, vlan_id, ip_address, gateway, netmask, pub_key_path):
# 	fname = 'tmp/fifo_vm.json'
# 	with open(fname, 'w') as fout:
# 		fout.write('{ "autoboot": true, "brand": "joyent", ')
# 		fout.write('"image_uuid": "d34c301e-10c3-11e4-9b79-5f67ca448df0", ')
# 		fout.write('"max_physical_memory": 2048, "cpu_cap": 100, "alias": "' + alias + '", ')
# 		fout.write('"quota": "10", "resolvers": [')
# 		first = True
# 		for resolver in resolvers:
# 			if first == True:
# 				fout.write('"' + resolver + '"')
# 				first = False
# 			else:
# 				fout.write(', "' + resolver + '"')
# 		fout.write('], ')
# 		fout.write('"nics": [ { "interface": "net0", "nic_tag": "admin", ')
# 		if (vlan_id == "1"):
# 			fout.write('"ip": "' + ip_address + '", "gateway": "' + gateway + '", "netmask": "' + netmask + '" ')
# 		else:
# 			fout.write('"vlan_id": ' + vlan_id + ', "ip": "' + ip_address + '", "gateway": "' + gateway + '", "netmask": "' + netmask + '" ')
# 		fout.write('} ], "customer_metadata": { ')
# 		fout.write('"root_authorized_keys": "')
# 		pub_key = open(pub_key_path, 'r')
# 		fout.write(pub_key.read().rstrip('\n').rstrip('\r'))
# 		fout.write('", ')
# 		fout.write('"user-script" : "/usr/sbin/mdata-get root_authorized_keys > ~root/.ssh/authorized_keys ; /usr/sbin/mdata-get root_authorized_keys > ~admin/.ssh/authorized_keys; chmod 700 /root/.ssh; chmod 600 /root/.ssh/authorized_keys" ')
# 		fout.write('} }')


def zone_definition(output_file = 'vm.json', mem = 1024, cpu = 100, disk = 10, alias = "", vlan_id = "1", ip_address = "", gateway = "", netmask = "", resolvers = ['8.8.8.8', '8.8.4.4'], pub_key_path = ""):
	with open(output_file, 'w') as fout:
		fout.write('{ "autoboot": true, "brand": "joyent", ')
		fout.write('"image_uuid": "' + stick_const.base64_img_uuid + '", ')
		fout.write('"max_physical_memory": ' + str(mem) + ', "cpu_cap": ' + str(cpu) + ', "alias": "' + alias + '", "hostname": "' + alias + '", ')
		fout.write('"quota": "' + str(disk) + '", "resolvers": [')
		first = True
		for resolver in resolvers:
			if first == True:
				fout.write('"' + resolver + '"')
				first = False
			else:
				fout.write(', "' + resolver + '"')
		fout.write('], ')
		fout.write('"nics": [ { "interface": "net0", "nic_tag": "admin", ')
		if (vlan_id == "1"):
			fout.write('"ip": "' + ip_address + '", "gateway": "' + gateway + '", "netmask": "' + netmask + '" ')
		else:
			fout.write('"vlan_id": ' + vlan_id + ', "ip": "' + ip_address + '", "gateway": "' + gateway + '", "netmask": "' + netmask + '" ')
		fout.write('} ], ')
		if len(pub_key_path) > 0:
			fout.write('"customer_metadata": { ')
			fout.write('"root_authorized_keys": "')
			pub_key = open(pub_key_path, 'r')
			fout.write(pub_key.read().rstrip('\n').rstrip('\r'))
			fout.write('", ')
			fout.write('"user-script" : "/usr/sbin/mdata-get root_authorized_keys > ~root/.ssh/authorized_keys ; chmod 700 /root/.ssh; chmod 600 /root/.ssh/authorized_keys" ')
			fout.write('  }')
		fout.write('}')


def pyfi_config(fifo_node, user, password):
	output_file = os.getenv("HOME") + '/.fifo'
	with open(output_file, 'w') as fout:
		fout.write('[GENERAL]\n')
		fout.write('active = fifo_default\n\n')
		fout.write('[fifo_default]\n')
		fout.write('apiversion = 0.1.0\n')
		fout.write('host = ' + fifo_node + '\n')
		fout.write('user = ' + user + '\n')
		fout.write('pass = ' + password + '\n')


'''

{
 "autoboot": true,
 "brand": "joyent",
 "image_uuid": "d34c301e-10c3-11e4-9b79-5f67ca448df0",
 "max_physical_memory": 2048,
 "cpu_cap": 100,
 "alias": "fifo",
 "quota": "40",
 "resolvers": [
  "8.8.8.8",
  "8.8.4.4"
 ],

 "nics": [
  {
   "interface": "net0",
   "nic_tag": "admin",
   "ip": "10.1.1.240",
   "gateway": "10.1.1.1",
   "netmask": "255.255.255.0"
  }
 ],
 "customer_metadata": {
    "root_authorized_keys": "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA8aQRt2JAgq6jpQOT5nukO8gI0Vst+EmBtwBz6gnRjQ4Jw8pERLlMAsa7jxmr5yzRA7Ji8M/kxGLbMHJnINdw/TBP1mCBJ49TjDpobzztGO9icro3337oyvXo5unyPTXIv5pal4hfvl6oZrMW9ghjG3MbIFphAUztzqx8BdwCG31BHUWNBdefRgP7TykD+KyhKrBEa427kAi8VpHU0+M9VBd212mhh8Dcqurq1kC/jLtf6VZDO8tu+XalWAIJcMxN3F3002nFmMLj5qi9EwgRzicndJ3U4PtZrD43GocxlT9M5XKcIXO/rYG4zfrnzXbLKEfabctxPMezGK7iwaOY7w== wooyay@houpla",
    "user-script" : "/usr/sbin/mdata-get root_authorized_keys > ~root/.ssh/authorized_keys ; /usr/sbin/mdata-get root_authorized_keys > ~admin/.ssh/authorized_keys"
 }
}








cd /opt
vi setupfifo.json
vmadm create -f setupfifo.json



zlogin <fifo-vm-uuid>
VERSION=rel
echo "http://release.project-fifo.net/pkg/${VERSION}/" >>/opt/local/etc/pkgin/repositories.conf
pkgin -fy up
pkgin install nginx fifo-snarl fifo-sniffle fifo-howl fifo-wiggle fifo-jingles
cp /opt/local/fifo-jingles/config/nginx.conf /opt/local/etc/nginx/nginx.conf

'''
