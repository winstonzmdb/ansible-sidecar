import argparse
import logging
from pprint import pprint
from helpers.constants import DELTA_PLAYBOOK_PATH
from helpers.fileIO import delete_folders_except_changes, get_abs_path, process_parameter

from helpers.watcher import start_monitoring
from helpers.ansible import create_new_ec2_playbook, create_new_playbook, call_playbook, get_playbook_tasks, roles_modified, task_modified

# define command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-p", "--playbook", help="path to the original playbook")
parser.add_argument("-i", "--image", help="name of the EC2 instance to use",)
parser.add_argument("-u", "--user", help="user on the image")
parser.add_argument("-k", "--identity_file", help="user identity file")
parser.add_argument('--skip', action='store_true', help='skip the full playbook execution')
args = parser.parse_args()

# set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


# assign command-line arguments to variables
playbook_relative_path = process_parameter(args,"playbook")
playbook_path = get_abs_path(playbook_relative_path)
image = process_parameter(args,"image")
user = process_parameter(args,"user")
identity_file = process_parameter(args,"identity_file")

# define the playbook command-line
identity_file_parameter_str = f"-e identity_file={identity_file}" if identity_file != None else ""
user_parameter_str = f"-e user={user}" if user != None else ""
template_playbook = "docker_playbook.yml" if image == None else f"ec2_playbook.yml -e target={image} {user_parameter_str} {identity_file_parameter_str}"

def initialize():
    logging.info(f"Intializing - Fetching the playbook")
    logging.info(f"Deleting cache...")
    delete_folders_except_changes()

    # Copy the source playbook to cache
    tasks = get_playbook_tasks(playbook_path)
    create_new_playbook(tasks,playbook_path)
    create_new_ec2_playbook(playbook_path)

    if args.image == "":
        logging.info(f"Intializing - Starting the container")
        call_playbook("init_docker_playbook.yml")

    if not args.skip:
        logging.info(f"Intializing - Running the Original Playbook")
        call_playbook(template_playbook)

# function to handle file system events
def handle_event(event):
    pprint(event)
    if event.is_directory: return
    # check if the modified file is the original playbook
    if not event.src_path.endswith(".yml"): return
    new_roles = []
    new_tasks = []

    if "/roles/" in event.src_path:
        logging.info(f"Detecting updated roles...")
        new_roles = roles_modified(playbook_path)
    
    # append task to roles. Helps maintain order without extra loops
    if event.src_path == playbook_path or len(new_roles):
        logging.info(f"Detecting updated tasks...")
        new_tasks = task_modified(playbook_path,new_roles)

    if len(new_tasks) == 0: 
        logging.info(f"No tasks updated")
        logging.info(f"Monitoring for changes...")
        return

    create_new_playbook(new_tasks,playbook_path)

    logging.info(f"Running the Updated Tasks")
    call_playbook(template_playbook)

if __name__ == "__main__":

    if not playbook_path:
        print("Please provide the path to the original playbook using the -p or --playbook flag.")
        exit()

    if image != None and user == None:
        print("Please provide a username to the instance using the -u or --user flag.")
        exit()

    initialize()
    start_monitoring(handle_event,playbook_path)