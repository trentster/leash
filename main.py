from flask import Flask, redirect, request, jsonify
#from json import dumps

import sys
import os
#import re
#import getpass
import string
#import copy
import random
import time
#import imp
import base64
import paramiko
from multiprocessing import Process


sys.path.append("lib")
import stick_actions
import stick_templates
import stick_utility
import stick_const


sys.path.append("deps/netaddr-0.7.13-py2.7.egg")
from netaddr import *

APP = Flask(__name__)

TEMP_DIR = os.getcwd() + "/tmp"

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

for the_file in os.listdir(TEMP_DIR):
    file_path = os.path.join(TEMP_DIR, the_file)
    try:
        if os.path.isfile(file_path):
            os.unlink(file_path)
    except Exception, error:
        pass

FETCH_DIR = '/opt/Fetch'


@APP.route('/')
def index():
    return redirect('/static/index.html')


@APP.route('/api/addKey', methods=['POST'])
def add_key():
    _key = request.form.get("key")
    if _key is not None:
        key = base64.b64decode(_key)
    key_type = request.form['type']

    if key_type == "hypervisor_priv":
        file_name = TEMP_DIR + "/hypervisor.key"

    elif key_type == "vm_priv":
        file_name = TEMP_DIR + "/vm.key"
    elif key_type == "vm_pub":
        file_name = TEMP_DIR + "/vm.pub"
    elif key_type == "vm_new":
        file_name = TEMP_DIR + "/vm.key"
        k = paramiko.RSAKey.generate(2048)
        k.write_private_key_file(file_name)
        file_name = TEMP_DIR + "/vm.pub"
        key = "ssh-rsa " + k.get_base64()
    else:
        return jsonify({'result': 'bad_request'})

    key_file = open(file_name, 'w')
    key_file.write(key)
    key_file.close()

    return jsonify({'result': 'ok'})


@APP.route('/api/checkHypervisor', methods=['POST'])
def interrogate_hypervisor():
    authenticator = request.form.get("password")
    if authenticator is not None:
        auth_type = "auth_type_password"
    else:
        auth_type = "auth_type_ssh"
        authenticator = TEMP_DIR + "/hypervisor.key"

    host = request.form['host']

    profile_results = stick_actions.profile_host("root", auth_type, authenticator, host)

    return_val = {}
    return_disk = {}
    return_mem = {}
    return_has_admin = {}
    return_platform_image_ok = {}
    return_threads = {}

    return_disk['value'] = str(profile_results['disk']) + 'G'
    if profile_results["disk"] >= stick_const.hyper_min_disk_min:
        return_disk['status'] = 'ok'
    else:
        return_disk['status'] = 'error'

    return_mem['value'] = str(profile_results['mem']) + 'G'
    if profile_results["mem"] >= stick_const.hyper_min_ram_min:
        return_mem['status'] = 'ok'
    else:
        return_mem['status'] = 'error'

    return_has_admin['value'] = profile_results['has_admin']
    if profile_results["has_admin"] == True:
        return_has_admin['status'] = 'ok'
    else:
        return_has_admin['status'] = 'error'

    return_platform_image_ok['value'] = profile_results['platform_image_ok']
    if profile_results["platform_image_ok"] == True:
        return_platform_image_ok['status'] = 'ok'
    else:
        return_platform_image_ok['status'] = 'warning'

    return_threads['value'] = profile_results['threads']
    return_threads['status'] = 'ok'


    return_val['disk'] = return_disk
    return_val['mem'] = return_mem
    return_val['has_admin'] = return_has_admin
    return_val['platform_image_ok'] = return_platform_image_ok
    return_val['threads'] = return_threads
    return_val['result'] = "ok"



    return jsonify(return_val)


@APP.route('/api/layoutVMs', methods=['POST'])
def layout_vms():

    hypervisors = []
    hypervisors = request.form.getlist("hypervisors[]")

    leoNodeCount = request.form.get("leoNodes")

    placements = stick_actions.recomend_vm_placements(hypervisors, leoNodeCount)

    if placements is None:
        return_val = {}
        return_val['result'] = "error"
        return

    return_val = {}
    return_val['placements'] = placements
    return_val['fifo_zone_count'] = stick_const.fifoZoneCount(len(hypervisors))
    return_val['result'] = "ok"

    return jsonify(return_val)




@APP.route('/api/install', methods=['POST'])
def install_fifo():
    authenticator = request.form.get("password")
    if authenticator is not None:
        auth_type = "auth_type_password"
    else:
        auth_type = "auth_type_ssh"
        authenticator = TEMP_DIR + "/hypervisor.key"

    hypervisors = []
    hypervisors = request.form.getlist("hypervisors[]")
    adminNetStart = request.form.get("adminNetStart")
    adminNetEnd = request.form.get("adminNetEnd")
    leoNodeCount = request.form.get("leoNodes")
    leoReplicaN = request.form.get("leoReplicaN")
    leoReplicaR = request.form.get("leoReplicaR")
    leoReplicaW = request.form.get("leoReplicaW")
    leoReplicaD = request.form.get("leoReplicaD")

    host_netconfig = stick_utility.network_host()
    assignableIpNetwork = IPNetwork(host_netconfig['gateway'] + '/' + host_netconfig['netmask'])
    assignableIpRange = list(iter_iprange(adminNetStart, adminNetEnd))

    fifo_cookie = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(20))
    leo_cookie = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(20))

        # hypervisors = []
        # hypervisors = request.form.getlist("hypervisors[]")
        #
        # leoNodeCount = request.form.get("leoNodes")
        #
        # placements = stick_actions.recomend_vm_placements(hypervisors, leoNodeCount)
        #
        # if placements is None:
        #     return_val = {}
        #     return_val['result'] = "error"
        #     return
        #



    print 'Profiling hypervisors...'
    hypervisor_profiles = []
    for hypervisor in hypervisors:
        hypervisor_profiles.append(stick_actions.profile_host(
            "root",
            auth_type,
            authenticator,
            hypervisor))

    print 'Generating VM sizes and placements...'
    hypervisor_sizing = {}
    for hypervisor in hypervisor_profiles:
        if hypervisor["mem"] >= stick_const.hyper_min_ram_good and \
           hypervisor["disk"] >= stick_const.hyper_min_disk_min:
            hypervisor_sizing[hypervisor["host"]] = stick_const.vm_sizing_good
        else:
            hypervisor_sizing[hypervisor["host"]] = stick_const.vm_sizing_min

    placements = stick_actions.recomend_vm_placements(hypervisors, leoNodeCount)

    if placements is None:
        return "error - could not create placements"





    # TODO: DEPLOY DATASET TO HYPERS

    print 'Creating first Fifo zone...'

    placement_index = next(
        index for (index, d) in enumerate(placements)
        if '1.fifo' in d)
    fifo_1_placement = placements[placement_index]['1.fifo']
    fifo_1_sizing = hypervisor_sizing[fifo_1_placement]

    stick_templates.zone_definition(
        '/tmp/1.fifo.json',
        fifo_1_sizing['fifo_zone_mem'],
        100,
        fifo_1_sizing['fifo_zone_disk'],
        '1.fifo',
        "1",
        adminNetStart,
        host_netconfig['gateway'],
        host_netconfig['netmask'],
        ['8.8.8.8', '8.8.4.4'],
        TEMP_DIR + '/vm.pub')

    if not stick_actions.create_zone("root@" + fifo_1_placement,
                                     '/tmp/1.fifo.json', False):
        print "There was an error createing the first machine."
        print "Aborting... Some changes possibly made to hypervisor: " + fifo_1_placement
        return "error - see logs"
    print 'VM "1.fifo" created on ' + fifo_1_placement

    print 'Configuring Fetch for Fifo'
    stick_actions.apply_properties(FETCH_DIR, 'fifo-sniffle',
                                   {'sniffle_cookie': fifo_cookie})
    stick_actions.apply_properties(FETCH_DIR, 'fifo-snarl', {'snarl_cookie': fifo_cookie})
    stick_actions.apply_properties(FETCH_DIR, 'fifo-howl', {'howl_cookie': fifo_cookie})
    stick_actions.apply_properties(FETCH_DIR, 'fifo-wiggle', {'wiggle_cookie': fifo_cookie})
    stick_actions.apply_properties(FETCH_DIR, 'fifo-chunter', {'chunter_cookie': fifo_cookie})

    print 'Installing fifo on vm'

    if not stick_actions.apply_role(FETCH_DIR, "fifo-sniffle",
                                    str(assignableIpRange[0]),
                                    TEMP_DIR + '/vm.key',
                                    'transport=paramiko') == True:
        return "error - could not apply sniffle role"

    if not stick_actions.apply_role(FETCH_DIR, "fifo-snarl",
                                    str(assignableIpRange[0]),
                                    TEMP_DIR + '/vm.key',
                                    'transport=paramiko') == True:
        return "error - could not apply snarl role"

    if not stick_actions.apply_role(FETCH_DIR, "fifo-howl",
                                    str(assignableIpRange[0]),
                                    TEMP_DIR + '/vm.key',
                                    'transport=paramiko') == True:
        return "error - could not apply howl role"

    if not stick_actions.apply_role(FETCH_DIR, "fifo-wiggle",
                                    str(assignableIpRange[0]),
                                    TEMP_DIR + '/vm.key',
                                    'transport=paramiko') == True:
        return "error - could not apply wiggle role"

    if not stick_actions.apply_role(FETCH_DIR, "fifo-jingles",
                                    str(assignableIpRange[0]),
                                    TEMP_DIR + '/vm.key',
                                    'transport=paramiko') == True:
        return "error - could not apply jingles role"

        #  svcadm clear wiggle; svcadm enable wiggle
        #pause for services to come online
    print 'Pausing for Fifo services to connect...'
    time.sleep(120)

    print 'Creating admin user in Fifo...'
    stick_actions.create_fifo_user(str(assignableIpRange[0]),
                                   "auth_type_ssh", TEMP_DIR + '/vm.key',
                                   "admin", "admin")

    print 'Creating pyfi config...'
    stick_templates.pyfi_config(adminNetStart, "admin", "admin")

    # TODO: add admin ssh key  - fifo

    print 'Creating admin network...'
    admin_network_uuid = stick_actions.create_fifo_network("Admin")
    if not admin_network_uuid:
        return "error - could not create admin network"


    #admin_network_ip = IPSet(IPRange(host_netconfig['gateway'], host_netconfig['netmask']))[0]
    admin_network_ip = str(assignableIpNetwork.network)

    admin_iprange_uuid = stick_actions.create_fifo_iprange(
        adminNetStart + "-" + adminNetEnd,
        admin_network_ip,
        host_netconfig['netmask'],
        host_netconfig['gateway'],
        adminNetStart,
        adminNetEnd,
        "admin")

    if not admin_iprange_uuid:
        return "error - could not create admin network ip range"

    admin_link_network_result = stick_actions.link_fifo_net_range(
        admin_network_uuid,
        admin_iprange_uuid)
    if not admin_link_network_result:
        return "error - could not add ip range to network"



    # TODO: create default packages  - fifo
    #
    # TODO: create fifo cluster  - fifo
    # add to fifo ring  - fabric
    # create fifo zones  - fifo
    # create leo cluster  - fifo
    print 'Configuring Fetch for Leo'
    leofs_manager_vars = {
        'leofs_cookie': leo_cookie,
        'leofs_master': 'manager0@' + str(assignableIpRange[1]),
        'leofs_slave': 'manager1@' + str(assignableIpRange[2]),
        'leofs_replicaN': str(leoReplicaN),
        'leofs_replicaR': str(leoReplicaR),
        'leofs_replicaW': str(leoReplicaW),
        'leofs_replicaD': str(leoReplicaD),
        'leofs_replicaRAR': '0'
    }

    leofs_gateway_vars = {
        'leofs_cookie': leo_cookie,
        'leofs_master': 'manager0@' + str(assignableIpRange[1]),
        'leofs_slave': 'manager1@' + str(assignableIpRange[2]),
    }

    leofs_storage_vars = {
        'leofs_cookie': leo_cookie,
        'leofs_master': 'manager0@' + str(assignableIpRange[1]),
        'leofs_slave': 'manager1@' + str(assignableIpRange[2]),
    }

    stick_actions.apply_properties(FETCH_DIR, 'leofs-manager', leofs_manager_vars)
    stick_actions.apply_properties(FETCH_DIR, 'leofs-gateway', leofs_gateway_vars)
    stick_actions.apply_properties(FETCH_DIR, 'leofs-storage', leofs_storage_vars)


    print 'Creating 1.manager.leofs zone...'
    X = next(index for (index, d) in enumerate(placements) if '1.manager.leofs' in d)
    leomngr_1_placement = placements[X]['1.manager.leofs']
    leomngr_1_sizing = hypervisor_sizing[leomngr_1_placement]

    stick_templates.zone_definition(
        '/tmp/1.manager.leofs',
        leomngr_1_sizing['leo_mngr_mem'],
        100,
        leomngr_1_sizing['leo_mngr_disk'],
        '1.manager.leofs',
        "1",
        str(assignableIpRange[1]),
        host_netconfig['gateway'],
        host_netconfig['netmask'],
        ['8.8.8.8', '8.8.4.4'],
        TEMP_DIR + '/vm.pub')

    if not stick_actions.create_zone("root@" + leomngr_1_placement, '/tmp/1.manager.leofs', False):
        return "error - could not create 1.manager.leofs"
    print 'VM "1.manager.leofs" created on ' + leomngr_1_placement



    print 'Creating 2.manager.leofs zone...'
    X = next(index for (index, d) in enumerate(placements) if '2.manager.leofs' in d)
    leomngr_2_placement = placements[X]['2.manager.leofs']
    leomngr_2_sizing = hypervisor_sizing[leomngr_2_placement]

    stick_templates.zone_definition(
        '/tmp/2.manager.leofs',
        leomngr_2_sizing['leo_mngr_mem'],
        100,
        leomngr_2_sizing['leo_mngr_disk'],
        '2.manager.leofs',
        "1",
        str(assignableIpRange[2]),
        host_netconfig['gateway'],
        host_netconfig['netmask'],
        ['8.8.8.8', '8.8.4.4'],
        TEMP_DIR + '/vm.pub')

    if not stick_actions.create_zone("root@" + leomngr_2_placement, '/tmp/2.manager.leofs', False):
        return "error - could not create 2.manager.leofs"
    print 'VM "2.manager.leofs" created on ' + leomngr_2_placement

    print 'Applying roles to LeoFS managers'
    if not (
            stick_actions.apply_role(
                FETCH_DIR,
                "leofs-manager",
                str(assignableIpRange[1]),
                TEMP_DIR + '/vm.key',
                'transport=paramiko nodename=manager0@' + str(assignableIpRange[1]))
        ) == True:
        return "error - could not apply Leofs manager role to manager 0"

    if not (
            stick_actions.apply_role(
                FETCH_DIR,
                "leofs-manager",
                str(assignableIpRange[2]),
                TEMP_DIR + '/vm.key',
                'transport=paramiko nodename=manager1@' + str(assignableIpRange[2]))
        ) == True:
        return "error - could not apply Leofs manager role to manager 1"


    print 'Creating 1.gateway.leofs zone...'
    X = next(index for (index, d) in enumerate(placements) if '1.gateway.leofs' in d)
    leogate_1_placement = placements[X]['1.gateway.leofs']
    leogate_1_sizing = hypervisor_sizing[leogate_1_placement]

    stick_templates.zone_definition(
        '/tmp/1.gateway.leofs',
        leogate_1_sizing['leo_gate_mem'],
        100,
        leogate_1_sizing['leo_gate_disk'],
        '1.gateway.leofs',
        "1",
        str(assignableIpRange[3]),
        host_netconfig['gateway'],
        host_netconfig['netmask'],
        ['8.8.8.8', '8.8.4.4'],
        TEMP_DIR + '/vm.pub')

    if not stick_actions.create_zone("root@" + leogate_1_placement,
                                     '/tmp/1.gateway.leofs', False):
        return "error - could not create 1.gateway.leofs"
    print 'VM "1.gateway.leofs" created on ' + leogate_1_placement

    print 'Applying roles to LeoFS gateway'
    if not (
            stick_actions.apply_role(
                FETCH_DIR,
                "leofs-gateway",
                str(assignableIpRange[3]),
                TEMP_DIR + '/vm.key',
                'transport=paramiko nodename=gateway0@' + str(assignableIpRange[3]))
        ) == True:
        return "error - could not apply Leofs gateway role to gateway 0"

    leo_vm_iterator = 0
    while leo_vm_iterator < int(leoNodeCount):
        leo_vm_iterator = leo_vm_iterator + 1
        node_name = str(leo_vm_iterator) + ".storage.leofs"

        print 'Creating ' + node_name + ' zone...'
        X = next(index for (index, d) in enumerate(placements) if node_name in d)
        leostorage_placement = placements[X][node_name]
        leostorage_sizing = hypervisor_sizing[leogate_1_placement]

        stick_templates.zone_definition(
            '/tmp/' + node_name,
            leostorage_sizing['leo_store_mem'],
            100,
            leostorage_sizing['leo_store_disk'],
            node_name,
            "1",
            str(assignableIpRange[(leo_vm_iterator + 3)]),
            host_netconfig['gateway'],
            host_netconfig['netmask'],
            ['8.8.8.8', '8.8.4.4'],
            TEMP_DIR + '/vm.pub')

        if not (
                stick_actions.create_zone("root@" + leostorage_placement,
                                          '/tmp/' + node_name, False)):
            return "error - could not create " + node_name
        print 'VM "' + node_name + '" created on ' + leostorage_placement
        role_options = ('transport=paramiko nodename=storage' +
                        str(leo_vm_iterator-1) +
                        '@' +
                        str(assignableIpRange[(leo_vm_iterator + 3)]))
        if not (
                stick_actions.apply_role(
                    FETCH_DIR,
                    "leofs-storage",
                    str(assignableIpRange[(leo_vm_iterator + 3)]),
                    TEMP_DIR + '/vm.key',
                    role_options)
            ) == True:
            return "error - could not apply Leofs storage role to storage " + str(leo_vm_iterator-1)


    print 'Starting LeoFS storage ring...'
    if not (
            stick_actions.start_leofs_storage(
                str(assignableIpRange[1]),
                "auth_type_ssh",
                TEMP_DIR + '/vm.key')
        ) == True:
        return "error - could not start Leofs storage ring"

    print 'Configuring Fifo to use LeoFS...'
    if not (
            stick_actions.init_fifo_leofs(
                str(assignableIpRange[0]),
                "auth_type_ssh",
                TEMP_DIR + '/vm.key',
                str(assignableIpRange[1]) + ".xip.io")
        ) == True:
        return "error - could not initialize leofs storage"

    if not (
            stick_actions.add_leofs_endpoint(
                str(assignableIpRange[1]),
                "auth_type_ssh",
                TEMP_DIR + '/vm.key',
                str(assignableIpRange[3]) + ".xip.io")
        ) == True:
        return "error - could not create endpoint in leofs"

    if not (
            stick_actions.config_fifo_sniffle(
                str(assignableIpRange[0]),
                "auth_type_ssh",
                TEMP_DIR + '/vm.key',
                'storage.s3.host',
                str(assignableIpRange[3]) + ".xip.io")
        ) == True:
        return "error - could not change leofs host in sniffle"


    ip_claim_iterator = 0
    while ip_claim_iterator < (int(leoNodeCount) + 4):
        stick_actions.claim_fifo_ip(
            str(assignableIpRange[0]),
            "auth_type_ssh",
            TEMP_DIR + '/vm.key',
            admin_iprange_uuid)
        ip_claim_iterator = ip_claim_iterator + 1


    stick_actions.create_hypervisor_inventory(FETCH_DIR, hypervisors)

    if auth_type == "auth_type_password":
        stick_actions.run_playbook_with_pass(
            FETCH_DIR + '/hypervisors.yml',
            FETCH_DIR + '/inventory/hypervisors',
            authenticator)
    else:
        stick_actions.run_playbook(FETCH_DIR + '/hypervisors.yml',
                                   FETCH_DIR + '/inventory/hypervisors')

    return jsonify({'result': 'ok'})




if __name__ == '__main__':
    APP.debug = True
    APP.run(host='0.0.0.0')
