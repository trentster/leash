from math import ceil
base64_img_uuid = 'd34c301e-10c3-11e4-9b79-5f67ca448df0'

initial_vms = ['1.fifo', '1.manager.leofs', '2.manager.leofs', '1.gateway.leofs', '1.storage.leofs']

hyper_min_ram_min = 8
hyper_min_disk_min = 10

hyper_min_ram_good = 32
hyper_min_disk_good = 100

vm_sizing_min = {
    'fifo_zone_disk' :   15,
    'fifo_zone_mem'  : 3072,
    'leo_mngr_disk'  :    5,
    'leo_mngr_mem'   :  512,
    'leo_gate_disk'  :    5,
    'leo_gate_mem'   : 1024,
    'leo_store_disk' :   40,
    'leo_store_mem'  : 1024,
}

vm_sizing_good = {
    'fifo_zone_disk' :   40,
    'fifo_zone_mem'  : 4096,
    'leo_mngr_disk'  :   10,
    'leo_mngr_mem'   : 1024,
    'leo_gate_disk'  :   10,
    'leo_gate_mem'   : 2048,
    'leo_store_disk' :   40,
    'leo_store_mem'  : 1024,
}


user_script = '"user-script" : "/usr/sbin/mdata-get root_authorized_keys > ~root/.ssh/authorized_keys ; /usr/sbin/mdata-get root_authorized_keys > ~admin/.ssh/authorized_keys; chmod 700 /root/.ssh; chmod 600 /root/.ssh/authorized_keys" '



def fifoZoneCount(hypervisorCount):
    if hypervisorCount == 1 or hypervisorCount == 2:
        return 1
    elif hypervisorCount == 3:
        return 3
    elif hypervisorCount == 4:
        return 4
    elif hypervisorCount > 1000: # formula below is only good for upto 1000
        return 50
    elif hypervisorCount > 4:
        a = 3.5986571221740977
        b = 0.10270953891690970
        c = -0.000056316603749656695
        result = a + (b * hypervisorCount) + (c * pow(hypervisorCount, 2))
        return ceil(result)
    return false
