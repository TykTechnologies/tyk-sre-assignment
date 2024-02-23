import socketserver
import json
from kubernetes import client, config
from http.server import BaseHTTPRequestHandler


class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Catch all incoming GET requests"""
        if self.path == "/healthz":
            self.healthz()
        elif self.path == "/k8shealth":
            self.k8s_health_check()
        elif self.path == "/deployments":
            self.deployments_info()
        else:
            self.send_error(404)

    def healthz(self):
        """Responds with the health status of the application"""
        self.respond(200, "ok")

    def k8s_health_check(self):
        """Performs a health check to verify communication with the Kubernetes API server"""
        try:
            config.load_kube_config()  # Load k8s configuration
            api_instance = client.CoreV1Api()
            api_instance.list_namespace()  # Perform a simple request to test connectivity
            self.respond(200, "Kubernetes API server is reachable")
        except Exception as e:
            # If an exception occurs, k8s api is not reachable
            self.respond(500, f"Failed to connect to Kubernetes API server: {str(e)}")

    def deployments_info(self):
      """Get information about deployments and check healthy pods"""
      api_client = client.ApiClient()
      deployments = get_deployments(api_client)
      deployment_info = []

      for deployment in deployments:
          desired_replicas = deployment.spec.replicas
          current_replicas = count_healthy_pods(api_client, deployment)
          status = "OK" if desired_replicas == current_replicas else "NOK"

          deployment_data = {
              "name": deployment.metadata.name,
              "namespace": deployment.metadata.namespace,
              "desired_replicas": desired_replicas,
              "current_replicas": current_replicas,
              "status": status
          }
          deployment_info.append(deployment_data)

      # Output each deployment info as newline
      deployment_lines = [json.dumps(info) for info in deployment_info]
      deployment_json = '\n'.join(deployment_lines)

      # Write JSON data directly to the response socket
      self.send_response(200)
      self.send_header('Content-Type', 'application/json')
      self.end_headers()
      self.wfile.write(bytes(deployment_json, "UTF-8"))
      
    def respond(self, status: int, content: str):
        """Writes content and status code to the response socket"""
        self.send_response(status)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()

        self.wfile.write(bytes(content, "UTF-8"))


def get_kubernetes_version(api_client: client.ApiClient) -> str:
    """
    Returns a string GitVersion of the Kubernetes server defined by the api_client.

    If it can't connect an underlying exception will be thrown.
    """
    version = client.VersionApi(api_client).get_code()
    return version.git_version


def start_server(address):
    """
    Launches an HTTP server with handlers defined by AppHandler class and blocks until it's terminated.

    Expects an address in the format of `host:port` to bind to.

    Throws an underlying exception in case of error.
    """
    try:
        host, port = address.split(":")
    except ValueError:
        print("invalid server address format")
        return

    with socketserver.TCPServer((host, int(port)), AppHandler) as httpd:
        print("Server listening on {}".format(address))
        httpd.serve_forever()

def get_deployments(api_client, namespace='default'):
    """Retrieve a list of all deployments in the Kubernetes cluster."""
    api_instance = client.AppsV1Api(api_client)
    try:
        deployments = api_instance.list_namespaced_deployment(namespace)
        return deployments.items
    except Exception as e:
        print(f"Error retrieving deployments: {e}")

def count_healthy_pods(api_client, deployment, namespace='default'):
    """Count the number of healthy pods for a given deployment."""
    api_instance = client.CoreV1Api(api_client)
    pod_labels = deployment.spec.selector.match_labels
    label_selector = ','.join([f"{key}={value}" for key, value in pod_labels.items()])

    try:
        pods = api_instance.list_namespaced_pod(namespace, label_selector=label_selector)
        healthy_count = sum(1 for pod in pods.items if is_pod_healthy(pod))
        return healthy_count
    except Exception as e:
        print(f"Error counting healthy pods for deployment {deployment.metadata.name}: {e}")
        return 0

def is_pod_healthy(pod):
    """Check if a pod is healthy."""
    if pod.status.phase != 'Running':
        return False
    if not pod.status.container_statuses:
        return False

    for container_status in pod.status.container_statuses:
        state = container_status.state
        if state.running is None or state.running.started_at is None:
            return False

    return True