# ansible-sidecar
This code is designed to automate the testing process for Ansible playbook changes. 

# process
It monitors an Ansible playbook and detects changes to yaml files that folder. When changes are detected, it runs the updated task or role on a container or AWS EC2 instance.

# dependencies
This application is written in Python. The following pip modules are also required.
```pip3 install watchdog ruamel.yaml```

# command-line parameters
playbook - `-p` - path to the original playbook.  
image - `-i` - name of the EC2 instance to use.  
user - `-u` - user on the image.  
identity_file - `-k` - user ssh identity file.  
skip - skip the inital full playbook execution   

# example - command-line
```python3 main.py -p /path/to/playbook/playbook.yml -i aws.dns.amazonaws.com -u Administrator```

# config file
The parameters can be stored in a config file (`config.ini`) instead of command-line parameters.

# example - config.ini
```
[default]
playbook = /path/to/playbook/playbook.yml
user = Administrator
image = aws.dns.amazonaws.com
```
