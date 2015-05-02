
def string_ansible_install_instructions():
	print("\n" + '*' * 80 + "\n" +
			"*  Ansible must be installed and in your PATH. Please take the following       *\n" +
			"*  steps to install on your system:                                            *\n" +
			"*                                                                              *\n" +
			"*  OSX (taken from https://devopsu.com/guides/ansible-mac-osx.html):           *\n" +
			"*      xcode-select --install  # Installs build tools                          *\n" +
			"*      sudo easy_install pip   # Install Pip                                   *\n" +
			"*      sudo pip install ansible --quiet # Install Ansible                      *\n" +
			"*  Upgrade Ansible on OSX at a later time with:                                *\n" +
			"*      sudo pip install ansible --upgrade                                      *\n" +
			"*                                                                              *\n" +
			"*  Ubuntu (taken from http://docs.ansible.com/):                               *\n" +
			"*       sudo apt-get install software-properties-common                        *\n" +
			"*       sudo apt-add-repository ppa:ansible/ansible                            *\n" +
			"*       sudo apt-get update                                                    *\n" +
			"*       sudo apt-get install ansible                                           *\n" +
			"*                                                                              *\n" +
			'*' * 80 + "\n\n")


def string_pyfi_install_instructions():
	print("\n" + '*' * 80 + "\n" +
			"*  The Fifo Console Client must be installed and in your PATH. Please take     *\n" +
			"*  the following steps to install on your system:                              *\n" +
			"*                                                                              *\n" +
			"*  OSX :                                                                       *\n" +
			"*      xcode-select --install  # Installs build tools                          *\n" +
			"*      git clone https://github.com/project-fifo/pyfi.git pyfi                 *\n" +
			"*      cd pyfi                                                                 *\n" +
			"*      make                                                                    *\n" +
			"*      [sudo] make install                                                     *\n" +
			"*                                                                              *\n" +
			"*  Ubuntu:                                                                     *\n" +
			"*       Todo                                                                   *\n" +
			"*                                                                              *\n" +
			'*' * 80 + "\n\n")

def string_fabric_install_instructions():
	print("\n" + '*' * 80 + "\n" +
			"*  The Fabric Python module must be installed on you system. Please take       *\n" +
			"*  the following steps to install on your system:                              *\n" +
			"*                                                                              *\n" +
			"*      sudo easy_install pip   # Install Pip                                   *\n" +
			"*      sudo pip install fabric                                                 *\n" +
			"*                                                                              *\n" +
			'*' * 80 + "\n\n")

def string_git_install_instructions():
	print("\n" + '*' * 80 + "\n" +
			"*  Git must be installed and in your PATH. Please take the following           *\n" +
			"*  steps to install on your system:                                            *\n" +
			"*                                                                              *\n" +
			"*  OSX:                                                                        *\n" +
			"*      xcode-select --install                                                  *\n" +
			"*                                                                              *\n" +
			"*  Ubuntu:                                                                     *\n" +
			"*       sudo apt-get install git                                               *\n" +
			"*                                                                              *\n" +
			'*' * 80 + "\n\n")


def new_line():
	print("")

def string_invalid_input():
	print("The input you provided is invalid.")

def string_verify_list():
	print("Please verify the following list.")

def string_prompt_ok():
	print("OK? (y/n) [n]")

def string_stick_init_welcome():
	print("\nWecome to Stick - the easy path to \"Go-Fetch\" Project Fifo.\n" +
			"There is a bit of information that we will need before we can start. " +
			"Due to the sensitive nature of some information collected if you exit this " +
			"script before it completes you will need to re-enter all info.\n")

def string_explain_admin_network():
	print("It is recommended that you run an \"Admin Network\" that is used only for " +
			"command/control communications. Becasue this network will need to allow Fifo " +
			"traffic we will need some information on it.\n\n" +
			"When a network is created for Fifo it expects to be able to assign every IP " +
			"address in the given range. Fifo does not do DHCP (which is likely how you " +
			"are booting SmartOS). For these reasons it is important to give some thought " +
			"to your network layout. The hypervisors need to be on the same subnet as the " +
			"Fifo nodes, but for orginzation purposes it is nice to keep groups of at least " +
			"/24. A nice way to deal with this is to use a /23 subnet and give the first " +
			"254 (a.b.c.1 used for gateway) for hypervisors and the second 254 (a.b.d.253 " +
			"is used for broadcast) for Fifo, and other management tools. Obviously how " +
			"you organize things is up to you, but you must be careful to not have the " +
			"same addresses handed out twice.")

def string_prompt_hypervisors():
	print("Please enter a list of your hypervisors' ip addresses, seperated by spaces. " +
			"i.e. 10.10.10.20 10.10.10.21 10.10.10.22")

def string_prompt_admin_network_ip():
	print("Please enter your Admin Network IP range in cidr format. i.e. 10.10.10.0/24")

def string_prompt_admin_network_vlan():
	print("Please enter the VLAN ID your Admin Network.")

def string_prompt_admin_network_start():
	print("Please enter the starting IP address for the Fifo managed portion of your Admin Network.")

def string_prompt_admin_network_end():
	print("Please enter the ending IP address for the Fifo managed portion of your Admin Network.")

def string_prompt_admin_network_gateway():
	print("Please enter the gateway IP address of your Admin Network.")

def string_prompt_admin_network_resolv():
	print("Please enter the DNS resolvers you would like your Fifo nodes to use, eperated by spaces [8.8.8.8 8.8.4.4]")

def string_explain_authentication():
	print("Next we need to collect some authenication information. This script will create " +
			"a single fifo admin user with full permisions. Additionally a user will be created " +
			"for Fifo to connect to LeoFS. You can add or change users with the " +
			"Web UI or CLI tools.")

def string_prompt_ssh_key():
	print("Please the path to your public ssh key. This will be added to Fifo zones [list keys in ~/.ssh]: ")

def string_prompt_admin_password():
	return "Please enter a password for the Fifo admin user: "

def string_prompt_verify_password():
	return "Please re-enter your password to verify: "

def string_passwords_dont_match():
	print("The passwords you entered do not match. Please try again.")

def string_explain_cookie():
	print("Fifo nodes use a secret cookie to ensure that all nodes making updates are part of the same cluster.")

def string_prompt_cookie():
	print("Please enter a string to be used as a cookie, or leave blank for a randomly generated cookie.")

def string_explain_smartos_passwrd():
	print("\n" + '*' * 80 + "\n" +
		"*  In order to create the initial smartos zone on your hypervisor Stick        *\n" +
		"*  will need the root user password, if you do not have ssh auth setup.        *\n" +
		"*                                                                              *\n" +
		"*  This password will not be stored (either locally or remotely).              *\n" +
		"*                                                                              *\n" +
		"*  Please enter your hypervisor root password at the next prompt.              *\n" +
		"*                                                                              *\n" +
		'*' * 80 + "\n\n")


def explain_point_of_no_return():
	print("OK. Now we have all the information that we need. Please confirm that the following settings are correct.")
	new_line()
	print("If these settings are not correct press Ctrl-C and start over. After verifying the input automated install will begin")



def logo():
	print """
                          _
                       ,:'/   _..._
                      // ( `""-.._.'
                      \| /    @\___
                      |     @      9
                      |            /
                      \_       .--'
                      (_'---'`)
                      / `'---`()              Welcome to Stick!
                    ,'        |    The easy path to "Go-Fetch" Project Fifo.
    ,            .'`          |
    )\       _.-'             ;
   / |    .'`   _            /
 /` /   .'       '.        , |
/  /   /           \   ;   | |
|  \  |            |  .|   | |
 \  `"|           /.-' |   | |
  '-..-\       _.;.._  |   |.;-.
        \    <`.._  )) |  .;-. ))
        (__.  `  ))-'  \_    ))'
            `'--"`       `"''"`
"""