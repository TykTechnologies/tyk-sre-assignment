import sys
import argparse

import logging
import time
import threading

from kubernetes import client, config

from app import app

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_k8s_api_health(api_client):
    """
    Periodically checks and logs the K8s api server health.
    """
    while True:
        try:
            version = app.get_kubernetes_version(api_client)
            logger.info("Kubernetes API server is healthy. Version: %s", version)
        except Exception as e:
            logger.error("Kubernetes API server health check failed: %s", e)
        time.sleep(5) #checks every 5s.


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tyk SRE Assignment",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-k", "--kubeconfig", type=str, default="",
                        help="path to kubeconfig, leave empty for in-cluster")
    parser.add_argument("-a", "--address", type=str, default=":8080",
                        help="HTTP server listen address")
    args = parser.parse_args()

    if args.kubeconfig != "":
        config.load_kube_config(config_file=args.kubeconfig)
    else:
        config.load_incluster_config()

    api_client = client.ApiClient()

    health_check_thread = threading.Thread(target=check_k8s_api_health, args=(api_client,))
    health_check_thread.daemon = True
    health_check_thread.start()

    try:
        version = app.get_kubernetes_version(api_client)
    except Exception as e:
        print(e)
        sys.exit(1)

    print("Connected to Kubernetes {}".format(version))

    try:
        app.start_server(args.address)
    except KeyboardInterrupt:
        print("Server terminated")
