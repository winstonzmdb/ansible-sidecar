import subprocess
import logging

def stop_container(image):
    subprocess.check_output(f"docker rm -f sidecar", shell=True)
    logging.info(f"Stopping container {image}.")

def start_container(image):
    stop_container(image)
    subprocess.check_output(f"docker run --rm -d --name sidecar {image}  tail -f /dev/null", shell=True).decode().strip()
    logging.info(f"Starting container {image}.")
