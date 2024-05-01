import os
import json
import logging
import traceback
from contextlib import contextmanager

import kubernetes as k8s


__API_GROUPS__ = dict(
    core=k8s.client.CoreV1Api,
    api_client=k8s.client.ApiClient,
    custom_object=k8s.client.CustomObjectsApi
)


@contextmanager
def kubernetes_api(group: str = 'core'):
    """
    Setup a connection to a kubeapi server.
    """

    if os.environ.get("KUBECONFIG", "") == "":
        k8s.config.load_incluster_config()
    else:
        k8s.config.load_kube_config()

    try:
        yield __API_GROUPS__[group]()
    except k8s.client.exceptions.ApiException as exception:
        try:
            body = json.loads(exception.body)
        except json.JSONDecodeError:
            logging.error("HTTP error not returning a JSON.")
            logging.error(traceback.print_exc())
            raise Exception(f"({exception.reason}) {exception.body}")
        else:
            logging.error(f"Error {exception.status} ({exception.reason})")
            message = body.get("message", "Kubernetes error")
            logging.error(message)
            logging.error(traceback.print_exc())
            raise Exception(message)






