from __future__ import with_statement
from fabric.api import *
from fabric.contrib.files import *
import ansible.runner
import ansible.playbook
from ansible import callbacks
from ansible import utils
import stick_const
import errno
import sys
import copy
import json
from multiprocessing import Process

import ansible.constants as C
C.HOST_KEY_CHECKING = False

env.reject_unknown_hosts = False
env.disable_known_hosts = True
env.abort_on_prompts = True

#==============================================================================
#
# Fact Gathering
#
#==============================================================================


def profile_host(user, auth_type, authenticator, host):

	if auth_type == "auth_type_password":
		env.password = authenticator
	elif auth_type == "auth_type_ssh":
		env.key_filename = authenticator
	else:
		return {"result": "bad"}

	env.user = user
	mem_result = execute(_check_mem_advail, hosts=host)
	threads_result = execute(_check_num_threads, hosts=host)
	disk_free_result = execute(_check_disk_free, hosts=host)
	admin_net_result = execute(_check_admin_network, hosts=host)
	platform_image_ok = execute(_check_platform_image, hosts=host)
	dns_lookup_ok = execute(_check_ip_lookup, host, hosts=host)

	return {"result": "ok", "host": host, "mem": mem_result[host], "threads": threads_result[host], "disk": disk_free_result[host], "has_admin": admin_net_result[host], "platform_image_ok": platform_image_ok[host], "dns_lookup_ok": dns_lookup_ok[host] }


def _check_mem_advail():
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		result = run('echo ::memstat | mdb -k | awk \'/Total/{print $3}\'')
		match = re.search(r'^[0-9]+$', result)
		if match:
		 	return int(match.group())/1000
		else:
			return None


def _check_num_threads():
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		result = run('psrinfo|wc -l|tr -d \' \'')
		match = re.search(r'^[0-9]+$', result)
		if match:
		 	return int(match.group())
		else:
			return None



def _check_disk_free():
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		result = run('df -k /zones | awk \'(NR==2){print $4}\'')
		match = re.search(r'^[0-9]+$', result)
		if match:
		 	return int(match.group())/1000000
		else:
			return None

def _check_platform_image():
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		result = run('TESTED_VERSIONS=20131003T221245Z\|20140124T065835Z\|20140221T042147Z\|20140404T041131Z\|20140404T041131Z\|20140404T001635Z\|20140501T225642Z\|20141225T170427Z\|20150108T111855Z; if (uname -a | egrep $TESTED_VERSIONS > /dev/null) ; then echo "1"; exit; fi; echo "0"')
		match = re.search(r'^[0-1]$', result)
		if match:
		 	if int(match.group()) == 1:
		 		return True
		 	else:
		 		return False
		else:
			return False

def _check_admin_network():
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		result = run('sysinfo -p | grep Names | awk -F= \'{print $2}\' | grep "^\'admin\'$" | wc -l')
		match = re.search(r'^[0-9]+$', result)
		if match:
		 	if int(match.group()) == 1:
		 		return True
		 	else:
		 		return False
		else:
			return False


def _check_admin_network_nic():
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		result = run('sysinfo -p | grep Network_Interface')
		match = re.search(r'^"/(?<=Network_Interface_)([a-zA-Z0-9]+)(?=_NIC_Names=\'admin\')/', result)
		if match:
		 	if int(match.group()) == 1:
		 		return True
		 	else:
		 		return False
		else:
			return False

def _check_ip_lookup(ipaddress):
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		result = run('nslookup ' + ipaddress + '.xip.io | grep Address | tail -1 | awk \'{print $2}\'')
		if result == ipaddress:
		 	return True
		else:
			return False


#==============================================================================
#
# VM Deployment
#
#==============================================================================

def create_zone(host, vm_def, ds_update = False):
	try:
		if ds_update:
			execute(_update_datasets, hosts=host)
			execute(_import_dataset, hosts=host)
		execute(_transfer_vm_def, vm_def, hosts=host)
		return execute(_create_vm, hosts=host)
	except VmCreationException:
		return False
	return False



def _update_datasets():
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		run('imgadm update')


def _import_dataset():
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		run('imgadm import ' + stick_const.base64_img_uuid)

def _install_dataset(manifest, disk):
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		run('imgadm install -m ' + manifest + ' -f ' + disk)


def _transfer_vm_def(vm_def):
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		put(vm_def, '/opt/stick_vm.json')


def _create_vm():
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		create_result = run('vmadm create -f /opt/stick_vm.json')
		create_result_vmid = re.findall(r'^(?:Successfully created VM) ([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', create_result)
		if len(create_result_vmid) < 1:
			print create_result
			raise VmCreationException()
			return False
		else:
			return create_result_vmid[0]

def _set_sshkey_vm(vm_uuid):
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		pub_key = open(pub_key_path, 'r')
		update_result = run('"customer_metadata": { "root_authorized_keys": "' + pub_key.read().rstrip('\n').rstrip('\r') + '", ' + stick_const.user_script + ' }')
		search_stream = "Successfully"
		if search_stream not in update_result:
			print update_result
			raise VmUpdateException()
			return False
		else:
			return True


#==============================================================================
#
# Local Go-Fetch Deployment
#
#==============================================================================

def deploy_fetch(local_go_fetch_dir, sniffle_params, snarl_params, howl_params, wiggle_params, chunter_params):
#def deploy_fetch(local_go_fetch_dir, sniffle_params):
	_clone_master(local_go_fetch_dir)
	apply_properties(local_go_fetch_dir, "fifo-sniffle", sniffle_params)
	apply_properties(local_go_fetch_dir, "fifo-snarl", snarl_params)
	apply_properties(local_go_fetch_dir, "fifo-howl", howl_params)
	apply_properties(local_go_fetch_dir, "fifo-wiggle", wiggle_params)
	apply_properties(local_go_fetch_dir, "fifo-chunter", chunter_params)



def _clone_master(local_go_fetch_dir):
	repo_location = local_go_fetch_dir + '/fetch'
	try:
		os.makedirs(repo_location)
	except OSError, e:
	    if e.errno != errno.EEXIST:
	        raise e
	    else:
	    	print "It looks like fetch is already deployed. Aborting download..."

	local("git clone https://github.com/Go-Fetch/Fetch.git " + repo_location )
	local("cd " + repo_location + "/roles; git submodule add https://github.com/Go-Fetch/fifo-sniffle.git")
	_create_playbook_for_role(repo_location, 'fifo-sniffle')
	local("cd " + repo_location + "/roles; git submodule add https://github.com/Go-Fetch/fifo-snarl.git")
	_create_playbook_for_role(repo_location, 'fifo-snarl')
	local("cd " + repo_location + "/roles; git submodule add https://github.com/Go-Fetch/fifo-howl.git")
	_create_playbook_for_role(repo_location, 'fifo-howl')
	local("cd " + repo_location + "/roles; git submodule add https://github.com/Go-Fetch/fifo-wiggle.git")
	_create_playbook_for_role(repo_location, 'fifo-wiggle')
	local("cd " + repo_location + "/roles; git submodule add https://github.com/Go-Fetch/fifo-jingles.git")
	_create_playbook_for_role(repo_location, 'fifo-jingles')
	local("cd " + repo_location + "/roles; git submodule add https://github.com/Go-Fetch/fifo-chunter.git")
	_create_playbook_for_role(repo_location, 'fifo-chunter')



#==============================================================================
#
# Ansible Actions
#
#==============================================================================

def apply_role(local_go_fetch_dir, role_name, host, priv_key = None, optional_paramaters = ''):
	from tempfile import NamedTemporaryFile

	if priv_key is not None:
		optional_paramaters += ' ansible_ssh_private_key_file=' + priv_key

	temp = NamedTemporaryFile(delete=False)

	temp.write("[" + role_name + "-nodes]\n")
	temp.write(host + " ansible_connection=ssh ansible_ssh_user=root ansible_python_interpreter=/opt/local/bin/python2.7 " + optional_paramaters + "\n")
	temp.close()

	stats = callbacks.AggregateStats()
	playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
	runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)

	pb = ansible.playbook.PlayBook(
	    playbook= local_go_fetch_dir + "/" + role_name + ".yml",
	    stats=stats,
	    callbacks=playbook_cb,
	    runner_callbacks=runner_cb,
	    host_list=temp.name
	)

	ansible.constants.HOST_KEY_CHECKING = False

	pr = pb.run()  # This runs the playbook

	if pr[host]['unreachable'] > 0 or pr[host]['failures'] > 0 :
		return False
	return True


def create_role_inventory(local_go_fetch_dir, role, hosts):
	inventory_file_name = local_go_fetch_dir + '/inventory/' + role
	inventory_file = open(inventory_file_name, 'w')
	inventory_file.write('[' + role + ']\n')
	for host in hosts:
		inventory_file.write(host + ' ansible_connection=ssh  ansible_ssh_user=root ansible_python_interpreter=/opt/local/bin/python2.7\n')

	inventory_file.close()


def create_hypervisor_inventory(local_go_fetch_dir, hypervisors):
	inventory_file_name = local_go_fetch_dir + '/inventory/hypervisors'
	inventory_file = open(inventory_file_name, 'w')
	inventory_file.write('[hypervisors]\n')
	for hypervisor in hypervisors:
		inventory_file.write(hypervisor + ' ansible_connection=ssh  ansible_ssh_user=root ansible_python_interpreter=/opt/local/bin/python2.7\n')

	inventory_file.write('\n[fifo-chunter-nodes:children]\n')
	inventory_file.write('hypervisors\n')
	inventory_file.close()


def run_playbook(playbook_name, inventory_file):
	stats = callbacks.AggregateStats()
	playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
	runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)

	pb = ansible.playbook.PlayBook(
	    playbook= playbook_name,
	    stats=stats,
	    callbacks=playbook_cb,
	    runner_callbacks=runner_cb,
	    host_list=inventory_file
	)

	pb.run()  # This runs the playbook


def run_playbook_with_pass(playbook_name, inventory_file, password):
	stats = callbacks.AggregateStats()
	playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
	runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)

	pb = ansible.playbook.PlayBook(
	    playbook= playbook_name,
	    stats=stats,
	    callbacks=playbook_cb,
	    runner_callbacks=runner_cb,
	    host_list=inventory_file,
	    remote_pass=password
	)

	pb.run()  # This runs the playbook



#==============================================================================
#
# Fifo Actions
#
#==============================================================================


def create_fifo_user(fifo_host, auth_type, authenticator, user_name, password, rights="...", realm="default"):
	if auth_type == "auth_type_password":
		env.password = authenticator
	elif auth_type == "auth_type_ssh":
		env.key_filename = authenticator
	else:
		return {"result": "bad"}

	new_user_result = execute(_fifo_new_user, realm, user_name, hosts=fifo_host)
	grant_user_result = execute(_fifo_grant, realm, user_name, rights, hosts=fifo_host)
	if grant_user_result == None:
		return None
	if  execute(_fifo_set_password, realm, user_name, password, hosts=fifo_host):
		return new_user_result
	return None

def create_fifo_network(name):
	return _fifo_create_network(name, True)

def create_fifo_iprange(name, network, netmask, gateway, first, last, tag, vlan = 0):
	return _fifo_create_iprange(name, network, netmask, gateway, first, last, tag, vlan, True)

def link_fifo_net_range(networkID, rangeID):
	return _fifo_add_range2network(networkID, rangeID, True)

def config_fifo_sniffle(fifo_host, auth_type, authenticator, key, value):
	if auth_type == "auth_type_password":
		env.password = authenticator
	elif auth_type == "auth_type_ssh":
		env.key_filename = authenticator
	else:
		return {"result": "bad"}
	update_setting_result = execute(_fifo_set_sniffle_config, key, value, hosts=fifo_host)
	if update_setting_result == None:
		return None
	return True

def init_fifo_leofs(fifo_host, auth_type, authenticator, s3_host):
	if auth_type == "auth_type_password":
		env.password = authenticator
	elif auth_type == "auth_type_ssh":
		env.key_filename = authenticator
	else:
		return {"result": "bad"}
	update_setting_result = execute(_fifo_leofs_init, s3_host, hosts=fifo_host)
	if update_setting_result == None:
		return None
	return True


def _fifo_set_sniffle_config(key, value):
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		result = run('sniffle-admin config set ' + key + ' ' + value)
		match = re.search(r'^Setting changed', result)
		if match:
		 	return True
		else:
			return None


def _fifo_leofs_init(s3_host):
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		result = run('/opt/local/sbin/sniffle-admin init-leofs ' + s3_host)
		match = re.search(r'^Created user fifo', result)
		if match:
		 	return True
		else:
			return None



def start_leofs_storage(leo_mngr, auth_type, authenticator):
	if auth_type == "auth_type_password":
		env.password = authenticator
	elif auth_type == "auth_type_ssh":
		env.key_filename = authenticator
	else:
		return {"result": "bad"}
	update_setting_result = execute(_leofs_start, hosts=leo_mngr)
	if update_setting_result == None:
		return None
	return True

def _leofs_start():
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		result = run('/opt/local/sbin/leofs-adm start')
		match = re.search(r'^OK', result)
		if match:
		 	return True
		else:
			return None


def add_leofs_endpoint(leo_mngr, auth_type, authenticator, endpoint_name):
	if auth_type == "auth_type_password":
		env.password = authenticator
	elif auth_type == "auth_type_ssh":
		env.key_filename = authenticator
	else:
		return {"result": "bad"}
	add_result = execute(_leofs_add_endpoint, endpoint_name, hosts=leo_mngr)
	if add_result == None:
		return None
	return True

def _leofs_add_endpoint(endpoint_name):
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		result = run('/opt/local/sbin/leofs-adm add-endpoint ' + endpoint_name)
		match = re.search(r'^OK', result)
		if match:
		 	return True
		else:
			return None


def claim_fifo_ip(fifo_host, auth_type, authenticator, range_uuid):
	if auth_type == "auth_type_password":
		env.password = authenticator
	elif auth_type == "auth_type_ssh":
		env.key_filename = authenticator
	else:
		return {"result": "bad"}
	# TODO: check output after FIFO-627 is resolved
	execute(_fifo_claim_ip, range_uuid, hosts=fifo_host)


def _fifo_claim_ip(range_uuid):
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		# TODO: check output after FIFO-627 is resolved
		run('/opt/local/sbin/fifoadm ipranges claim ' + range_uuid)
		return True



    # TODO: create package  - fifo
    # TODO: create fifo cluster  - fifo

def _fifo_new_user(realm, user_name):
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		create_result = run('fifoadm users add ' + realm + ' ' + user_name)
		create_result_userid = re.findall(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', create_result)
		if len(create_result_userid) < 1:
			return False
		else:
			return create_result_userid[0]


def _fifo_grant(realm, user_name, rights):
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		result = run('fifoadm users grant ' + realm + ' ' + user_name + ' ' + rights)
		match = re.search(r'^Granted', result)
		if match:
		 	return True
		else:
			return None

def _fifo_set_password(realm, user_name, password):
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		result = run('fifoadm users passwd ' + realm + ' ' + user_name + ' ' + password)
		match = re.search(r'^Password successfully changed', result)
		if match:
		 	return True
		else:
			return None

def _fifo_create_network(name, ignore_ssl = False):
		run_opts = ""
		if ignore_ssl:
			run_opts = "--unsafe "
		create_result = local('fifo ' + run_opts + ' networks create ' + name, capture=True)
		create_result_networkid = re.findall(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', create_result)
		if len(create_result_networkid) < 1:
			return False
		else:
			return create_result_networkid[0]

def _fifo_create_iprange(name, network, netmask, gateway, first, last, tag, vlan = 0, ignore_ssl = False):
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		run_opts = ""
		if ignore_ssl:
			run_opts = "--unsafe "
		run_cmd = ('fifo ' + run_opts + 'ipranges create ' + name + ' --network=' + network + ' --netmask=' + netmask + ' --gateway=' + gateway + ' --first=' + first + ' --last=' + last + ' --tag=' + tag)
		if vlan > 0:
			run_cmd += ' -v ' + vlan

		create_result = local(run_cmd, capture=True)
		create_result_rangeid = re.findall(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', create_result)
		if len(create_result_rangeid) < 1:
			return False
		else:
			return create_result_rangeid[0]


def _fifo_add_range2network(networkID, rangeID, ignore_ssl = False):
	with settings(
		hide('warnings', 'running', 'stdout', 'stderr'),
		warn_only=True
	):
		run_opts = ""
		if ignore_ssl:
			run_opts = "--unsafe "
		result = local('fifo ' + run_opts + ' networks add-range ' + networkID + ' ' + rangeID, capture=True)
		match = re.search(r'^Successfully', result)
		if match:
		 	return True
		else:
			return None


#==============================================================================
#
# Utils
#
#==============================================================================

def apply_properties(local_go_fetch_dir, repo_name, prop_list):
	for key, value in prop_list.iteritems():
		_repo_set_var(local_go_fetch_dir, repo_name, key, value)

def _repo_set_var(local_go_fetch_dir, repo_name, var_name, var_value):
	var_file = local_go_fetch_dir + '/roles/' + repo_name + '/vars/main.yml'

	f1 = open(var_file, 'r')
	f2 = open(var_file + '.tmp', 'w')

	for line in f1:
	    f2.write(line.replace("<<" + var_name + ">>", var_value))

	f1.close()
	f2.close()
	os.remove(var_file)
	os.rename(var_file + ".tmp", var_file)

def _create_playbook_for_role(fetch_dir, role_name):
	playbook_file_name = fetch_dir + '/' + role_name + '.yml'
	playbook_file = open(playbook_file_name, 'w')
	playbook_file.write('- hosts: ' + role_name + '-nodes\n')
	playbook_file.write('  roles:\n')
	playbook_file.write('    - ' + role_name + '\n')
	playbook_file.close()


def ssh_login(host, username, password):
	env.user = username
	env.password = password
	execute(_ssh_login, hosts=host)


def _ssh_login():
		run('echo " " > /dev/null')


def recomend_vm_placements(hypervisors = [], leoNodeCount = 1):

	if len(hypervisors) < 1:
		return None

	vms = copy.deepcopy(stick_const.initial_vms)
	placements = []
	i = 1
	k = 0

	while i < int(leoNodeCount):
		i = i + 1
		vms.append( str(i) + ".storage.leofs")

	for vm in vms:
		placement = {}
		placement[vm] = hypervisors[k]
		placements.append(placement.copy())
		k += 1
		if k >= len(hypervisors):
			k = 0

	return placements



#==============================================================================
#
# Exceptions
#
#==============================================================================


class VmCreationException(Exception):
    pass

class VmUpdateException(Exception):
    pass
