import subprocess
import logging

def run_playbook(file_path):
    # Run the new playbook
    logging.info(f"Running updated tasks")
    command = f"ansible-playbook {file_path}"
    logging.info(command)
    subprocess.call(command, shell=True)
