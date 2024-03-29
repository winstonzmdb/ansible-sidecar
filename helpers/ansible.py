# function to create a new playbook file with the changed task and run it
import os
import copy
import logging
from ruamel.yaml import YAML
yaml = YAML()
import shutil
import subprocess
from helpers.constants import DELTA_PLAYBOOK_PATH, EC2_PLAYBOOK_PATH, NEW_PLAYBOOK_PATH
from helpers.fileIO import check_list_overlap, check_list_variable_existance, copy_roles_folder, flatten_dict, hash_file, read_playbook, write_playbook

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
    def diff_append(task,var=None):
        diff_tasks.append(task)
        if var == None: return
        if isinstance(var, str):
            diff_vars.append(var)
            return
        diff_vars.extend(list(var))

    # Load the contents of the two playbooks
    tasks1 = get_playbook_tasks(original_playbook_path)
    tasks2 = get_playbook_tasks(DELTA_PLAYBOOK_PATH)

    # Initialize lists and dictionary for variable tracking
    diff_tasks = []
    diff_vars = []
    all_vars_tasks = get_all_variable_tasks(tasks1)
    all_vars = list(all_vars_tasks.keys())

    for task in tasks1:
        # Check if task contains variables in the diff_vars list
        if task_contains_variable(diff_vars,task) != None:
            diff_append(task)
            continue

        # Check if task is not updated
        if task in tasks2 and task not in new_roles: continue

        # Check if task updates variables
        updated_vars = get_updated_variables(task)
        if len(updated_vars):
            diff_append(task,updated_vars)
            continue

        # Append the required set_facts/register tasks
        found_var = task_contains_variable(all_vars,task)
        if found_var not in diff_vars and found_var in all_vars_tasks:
            diff_append(all_vars_tasks[found_var],found_var)

        diff_append(task)

    return diff_tasks


def get_all_variable_tasks(tasks):
    all_vars_tasks = {}
    for task in tasks:
        updated_vars = get_updated_variables(task)
        if len(updated_vars):
            for updated_var in updated_vars:
                all_vars_tasks[updated_var] = task
    return all_vars_tasks

def task_contains_variable(vars,task):
    flat = flatten_dict(task)
    values = (list(flat.values()))
    return check_list_variable_existance(vars,values)

def get_updated_variables(task):
    if ("register" in task):
        return [task["register"]]
    if ("set_fact" in task):
        return list(task["set_fact"].keys())
    return []

def retrieve_roles(playbook_path,role_name):
    playbook = get_playbook_tasks(playbook_path)
    role_tag = "include_role"
    for task in playbook:
        if role_tag in task and task[role_tag]["name"] == role_name:
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

add_host_play = {
    'hosts': 'localhost',
    'gather_facts': False,
    'ignore_errors': True,
    'tasks': [{
        'name': 'Add EC2 instance as host',
        'ansible.builtin.add_host': {
            'name': '{{ target }}',
            'groups': 'ec2',
            'ansible_user': '{{ user }}'
        }
    }]
}

def create_new_ec2_playbook(playbook_path):
    # Load the original playbook
    playbook = read_playbook(playbook_path)

    # Extract the host vars from the original playbook
    for section in ['tasks', 'roles']:
        playbook.pop(section, None)

    playbook['hosts'] = 'ec2'
    playbook['roles'] = [{'role': 'changes'}]
    new_playbook = copy.deepcopy(playbook)

    # Insert the new play at the beginning of the original playbook
    new_playbook = [add_host_play,playbook]
    # Save the updated playbook to a file
    with open(EC2_PLAYBOOK_PATH, 'w') as file:
        yaml.dump(new_playbook, file)
