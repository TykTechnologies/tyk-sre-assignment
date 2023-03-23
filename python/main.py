import sys
import argparse

from kubernetes import client, config

from app import app


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
