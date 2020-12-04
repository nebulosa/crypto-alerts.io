VAGRANTFILE_API_VERSION   = '2'
Vagrant.require_version '>= 1.8.2'

CURRENT_DIR = File.expand_path(File.dirname(__FILE__))
DIRNAME     = File.basename(CURRENT_DIR)

hosts = [
    #10.10.10.1 is configured as bridged between the host and 10.10.1.x guests
    {
        :name   => "dev.crypto-alerts.io",
        :box    => "minos/core-18.04",        #verify docker/docker-compose installation works
        #:box    => "minos/core-18.04-docker",  #iterate faster over app's provisioning bits
        :groups => ["docker", "app" ],
        :ram    => "512", :cpus  => "1",
        :ip     => "10.10.10.11",
    },
]

host_os  = RbConfig::CONFIG['host_os']
if host_os =~ /linux/
    all_cpus = `nproc`.to_i
elsif host_os =~ /darwin/
    all_cpus = `sysctl -n hw.ncpu`.to_i
else #windows?
    all_cpus = `wmic cpu get NumberOfCores`.split("\n")[2].to_i
end

default_ram  = '512' #MB
default_cpu  = '50'  #%
default_cpus = all_cpus || '1'

#vagrant-hostmanager-ext automatically edit hosts files to let vms communicate by domain
raise "vagrant-hostmanager-ext plugin must be installed: $ vagrant plugin install vagrant-hostmanager-ext" unless Vagrant.has_plugin? "vagrant-hostmanager-ext"

raise "cannot continue without './.env' file" unless File.exists?(".env")
raise "cannot continue without './.vault_pass.txt' file" unless File.exists?(".vault_pass.txt")

#cross-platform way of finding an executable in the $PATH.
def which(cmd)
    exts = ENV['PATHEXT'] ? ENV['PATHEXT'].split(';') : ['']
    ENV['PATH'].split(File::PATH_SEPARATOR).each do |path|
        exts.each do |ext|
            exe = File.join(path, "#{cmd}#{ext}")
            return exe if File.executable?(exe) && !File.directory?(exe)
        end
    end
    nil
end

raise "cannot continue without 'ansible' < 2.4.2.0: "     \
      "$ sudo add-apt-repository ppa:ansible/ansible; "   \
      "sudo apt-get update; sudo apt-get install ansible" \
    unless which('ansible-playbook')

host_counter = 0; Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    hosts.each do |host|
        config.vm.define host[:name] do |machine|
            machine.vm.box      = host[:box]
            machine.vm.box_url  = host[:box_url] if host[:box_url]
            machine.vm.hostname = host[:name]

            machine.vm.network :private_network, ip: host[:ip]

            machine.vm.provider "virtualbox" do |vbox|
                vbox.name = host[:name]
                vbox.linked_clone = true
                vbox.customize ["modifyvm", :id, "--memory", host[:ram] || default_ram ]          #MB
                vbox.customize ["modifyvm", :id, "--cpuexecutioncap", host[:cpu] || default_cpu ] #%
                vbox.customize ["modifyvm", :id, "--cpus", host[:cpus] || default_cpus ]
                vbox.customize ["modifyvm", :id, "--usb",   "off"]  #disable usb/audio for good
                vbox.customize ["modifyvm", :id, "--audio", "none"]
            end

            #echo cmds, lambda syntax: http://stackoverflow.com/questions/8476627/what-do-you-call-the-operator-in-ruby
            #why not UPPERCASE?: https://ruby-doc.org/docs/ruby-doc-bundle/UsersGuide/rg/constants.html
            cmd_script_root        = -> (cmd) { machine.vm.provision 'shell', path:   cmd, name: cmd, privileged: true  }
            cmd_script             = -> (cmd) { machine.vm.provision 'shell', path:   cmd, name: cmd, privileged: false }
            cmd_inline_root        = -> (cmd) { machine.vm.provision 'shell', inline: cmd, name: cmd, privileged: true  }
            cmd_inline             = -> (cmd) { machine.vm.provision 'shell', inline: cmd, name: cmd, privileged: false }
            cmd_script_always_root = -> (cmd) { machine.vm.provision 'shell', path:   cmd, name: cmd, run: "always", privileged: false }
            cmd_script_always      = -> (cmd) { machine.vm.provision 'shell', path:   cmd, name: cmd, run: "always", privileged: false }

            #authorize default public ssh key
            cmd_inline_root.call("mkdir -p /root/.ssh/")
            cmd_inline.call     ("mkdir -p /home/vagrant/.ssh/")
            if File.file?("#{Dir.home}/.ssh/id_rsa.pub")
                ssh_pub_key = File.readlines("#{Dir.home}/.ssh/id_rsa.pub").first.strip
                cmd_inline_root.call("printf '\\n%s\\n' '#{ssh_pub_key}' >> /root/.ssh/authorized_keys")
                cmd_inline.call     ("printf '\\n%s\\n' '#{ssh_pub_key}' >> /home/vagrant/.ssh/authorized_keys")
            end

            #copy private ssh key
            if File.file?("#{Dir.home}/.ssh/id_rsa")
                machine.vm.provision "file",  source: "~/.ssh/id_rsa", destination: "/home/vagrant/.ssh/id_rsa"
                cmd_inline.call("chown vagrant:vagrant /home/vagrant/.ssh/id_rsa")
                cmd_inline.call("chmod 600 /home/vagrant/.ssh/id_rsa")
            else
                if File.file?("provision/ansible/ansible-local/ansible-local.pub")
                    ssh_pub_key = File.readlines("provision/ansible/ansible-local/ansible-local.pub").first.strip
                    cmd_inline_root.call("printf '\\n%s\\n' '#{ssh_pub_key}' >> /root/.ssh/authorized_keys")
                    cmd_inline.call     ("printf '\\n%s\\n' '#{ssh_pub_key}' >> /home/vagrant/.ssh/authorized_keys")
                    machine.vm.provision "file",
                        source:      "provision/ansible/ansible-local/ansible-local.priv",
                        destination: "/home/vagrant/.ssh/id_rsa"
                    cmd_inline.call     ("chown vagrant:vagrant /home/vagrant/.ssh/id_rsa")
                    cmd_inline.call     ("chmod 600 /home/vagrant/.ssh/id_rsa")
                end
            end

            #copy gitconfig
            if File.file?("#{Dir.home}/.gitconfig")
                machine.vm.provision "file",  source: "~/.gitconfig", destination: "/home/vagrant/.gitconfig"
            end

            #only execute ansible when all hosts are ready
            host_counter = host_counter + 1; if File.file?("provision/ansible/app.yml")
                if host_counter == hosts.length

                    #create ansible inventory groups to apply group_vars
                    ansible_groups = {}; for host in hosts do
                        for group in host[:groups] do
                            if ansible_groups.has_key?(group)
                                #append to list
                                ansible_groups[group].push(host[:name])
                            else
                                ansible_groups[group] = [host[:name]]
                            end
                        end
                    end

                    machine.vm.provision "ansible" do |ansible|
                        ansible.playbook    = "provision/ansible/app.yml"
                        ansible.config_file = "provision/ansible/ansible.cfg"
                        ansible.extra_vars  = "provision/ansible/inventories/vagrant/group_vars/all/vars.yml"
                        ansible.limit       = "all"
                        ansible.groups      = ansible_groups
                        #ansible.verbose    = "vvv"
                        #ansible.galaxy_role_file   = "requirements.yml"
                        ansible.vault_password_file = ".vault_pass.txt"
                        ansible.raw_arguments  = [
                            "--extra-vars=@provision/ansible/inventories/vagrant/group_vars/all/vault.yml"
                        ]
                        ansible.raw_arguments += Shellwords.shellsplit(ENV['ANSIBLE_ARGS']) if ENV['ANSIBLE_ARGS']
                    end
                end
            end
        end
    end

    config.hostmanager.enabled      = true
    config.hostmanager.manage_host  = true
    config.hostmanager.manage_guest = true
end

# vi: set ft=ruby :
