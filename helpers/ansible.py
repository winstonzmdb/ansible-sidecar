# function to create a new playbook file with the changed task and run it
import os
import copy
import logging
from pprint import pprint
from ruamel.yaml import YAML
yaml = YAML()
import shutil
import subprocess
from helpers.constants import DELTA_PLAYBOOK_PATH, EC2_PLAYBOOK_PATH, NEW_PLAYBOOK_PATH
from helpers.fileIO import copy_roles_folder, hash_file, read_playbook, write_playbook

# function that writes the task to the cache playbook
def create_new_playbook(tasks,original_playbook_path):
    write_playbook(tasks,NEW_PLAYBOOK_PATH)
    copy_roles_folder(original_playbook_path)
    shutil.copyfile(original_playbook_path, DELTA_PLAYBOOK_PATH)

def copy_task(task):
    new_task = {}
    for key, value in task.items():
        if key != "name":
            new_task[key] = value
    return {
                "name": task["name"],
                **new_task
            }

# function to check if a task has been modified
def task_modified(original_playbook_path,new_roles):

    # Load the contents of the two playbooks
    tasks1 = get_playbook_tasks(original_playbook_path)
    tasks2 = get_playbook_tasks(DELTA_PLAYBOOK_PATH)

    # Find the tasks that are different
    diff_tasks = [task for task in tasks1 if task not in tasks2 or task in new_roles]
    return diff_tasks

def retrieve_roles(playbook_path,role_name):
    playbook = get_playbook_tasks(playbook_path)
    role_tag = "include_role"
    for task in playbook:
        if task[role_tag]["name"] == role_name:
            return task

# Function to extract the roles and their corresponding tasks from a playbook
def extract_roles(playbook_path):
    playbook = get_playbook_tasks(playbook_path)
    root_path = os.path.dirname(playbook_path)
    role_tag = "include_role"
    roles = {}
    for task in playbook:
        if role_tag in task:
            role_name = task[role_tag]["name"]
            role_path = root_path + "/roles/" + role_name + "/tasks"
            roles[role_name] = generate_folder_hash(role_path)
    return roles

def generate_folder_hash(path):
    hashes = []
    for filename in os.listdir(path):
        filepath = os.path.join(path, filename)
        file_hash = generate_file_hash(filepath, ".yml")
        if (file_hash != None): hashes.append(file_hash)
    return hashes

def generate_file_hash(path,ext):
    if path.endswith(ext):
        return hash_file(path)
    return None
    
# Function to identify the roles that have tasks that changed
def roles_modified(original_playbook_path):
    roles = extract_roles(DELTA_PLAYBOOK_PATH)
    updated_roles = extract_roles(original_playbook_path)
    changed_roles = []
    for role in roles:
        if role in updated_roles and roles[role] != updated_roles[role]:
            changed_roles.append(retrieve_roles(original_playbook_path,role))
    return changed_roles

# function to check if a task has been modified
def get_playbook_tasks(original_playbook_path):

    # Load the contents of the playbooks
    playbook1 = read_playbook(original_playbook_path)
    # Extract the tasks from the playbook
    tasks = playbook1["tasks"]

    return tasks

def call_playbook(playbook):
    command = f"ansible-playbook {playbook}"
    logging.info(f"Ansible command: {command}")
    subprocess.check_call(command, shell=True)
    logging.info(f"Monitoring for changes...")


def create_new_ec2_playbook(playbook_path):
    # Load the original playbook
    playbook = read_playbook(playbook_path)

    # Extract the host vars from the original playbook
    for section in ['tasks', 'roles']:
        playbook.pop(section, None)

    playbook['hosts'] = 'ec2'
    playbook['roles'] = [{'role': 'changes'}]
    new_playbook = copy.deepcopy(playbook)

    # Add a new play to the beginning of the playbook
    add_host_play = {
        'hosts': 'localhost',
        'gather_facts': False,
        'tasks': [{
            'name': 'Add EC2 instance as host',
            'ansible.builtin.add_host': {
                'name': '{{ target }}',
                'groups': 'ec2',
                'ansible_user': '{{ user }}'
            }
        }]
    }

    # Insert the new play at the beginning of the original playbook
    new_playbook = [add_host_play,playbook]
    # Save the updated playbook to a file
    with open(EC2_PLAYBOOK_PATH, 'w') as file:
        yaml.dump(new_playbook, file)
