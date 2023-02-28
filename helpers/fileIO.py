import os
import shutil
import hashlib
import configparser
from ruamel.yaml import YAML
from pathlib import Path
yaml = YAML()
roles_path = os.getcwd()+"/roles"

def write_playbook(playbook, path):
  with open(path, "w") as f:
      yaml.indent(sequence=4, offset=2)
      out = Path(path)
      yaml.dump(playbook, out)

def read_playbook(path):
    # read the original playbook file
    with open(path, "r") as f:
        playbook_content = f.read()

    # load the playbook content as a dictionary
    playbook = yaml.load(playbook_content)
    return playbook[0]

def process_parameter(args,param):
    value = getattr(args, param)
    if value: return value
    
    # If the parameter was not provided, read the default value from the config file
    config = configparser.ConfigParser()
    config.read('config.ini')
    try:
        return config.get('default', param)
    except configparser.NoOptionError:
        return None

def delete_folders_except_changes():
    # Get the list of folders in the directory
    folders = os.listdir(roles_path)
    
    # Loop through the folders and delete any that are not named 'changes'
    for folder in folders:
        if folder != 'changes':
            folder_path = os.path.join(roles_path, folder)
            if os.path.isdir(folder_path):
                shutil.rmtree(folder_path)
                
def copy_roles_folder(playbook_path):
    root_folder_path = os.path.dirname(playbook_path)
    shutil.copytree(root_folder_path+"/roles", os.getcwd()+"/roles", dirs_exist_ok = True)

# Function to compute the SHA-256 hash of a file
def hash_file(filename):
    hasher = hashlib.sha256()
    with open(filename, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()