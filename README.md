# Virtual Kubelet Test Set

The *Virtual Kubelet Test Set* provides a simple templated infrastructure
to collect, run and report functionality tests for Virtual Kubelet providers.
It is being developed in the context of the Proof-of-Concept on the adoption
of the [InterLink](https://github.com/interTwin-eu/interLink) abstractions 
to serverless containers to ease the validation of the various backends.


[InterLink](https://github.com/interTwin-eu/interLink) is a toolset to
provide an abstraction for the execution of a Kubernetes pod on any remote 
resource capable of managing a Container execution lifecycle.

It is composed of a *client* translating the kube-apiserver requests into
InterLink APIs and forwarding them towards a remote *target*, that translate
them back to interact with some container lifecycle management tool.
To decouple the management of the container lifecycle from the APIs, the former
is designed to be implemented in an independent *container plugin*, often
called *the sidecar* in the InterLink jargon.

The *Virtual Kubelet Test Set* (`vk-test-set`) repository aims at providing a standard set 
of tools to validate the functionality of the sidecar, by submitting Pods
of increasingly complexity. It features:
 * a unit-test infrastructure based on [`pytest`](https://docs.pytest.org/en/8.2.x/);
 * a manifest template engine relying on [`jinja2`](https://jinja.palletsprojects.com/en/2.10.x/);
 * an interface to a Kubernetes cluster relying on the official 
   [Kubernetes Python Client](https://github.com/kubernetes-client/python);
 * a test validation infrastructure based on regular expressions, configured in the 
   same file as the manifest template and parsed via 
   [`pydantic`](https://docs.pydantic.dev/latest/).

## Manifest templates
Templates are stored in `vktestset/templates` and shipped with the 
Python package. 

Each template is composed of three sections:
```yaml
#
# The template documentation
# 

The Kubernetes manifests

# VALIDATION

The validation configuration

```

Note in particular, that the line `# VALIDATION` separates the Kubernetes
manifests from the validation.

Below is reported the template for a *hello world* pod.

```yaml
## Hello world
##
## First simple test to ensure the communication is open and a simple
## echo command can be executed.
## Launches a pod printing "hello world" in the log.

apiVersion: v1
kind: Pod
metadata:
  name: hello-world-{{ uuid }}
  namespace: {{ namespace }}
  annotations: {{ annotations | tojson }}

spec:
  restartPolicy: Never
  nodeSelector:
    kubernetes.io/hostname: {{ target_node }}

  containers:
  - name: hello-world
    image: ghcr.io/grycap/cowsay 
    command: ["/bin/bash", "-c"]
    args: ["echo hello world"]
    imagePullPolicy: Always
    
  dnsPolicy: ClusterFirst

  tolerations: {{ tolerations | tojson }}

################################################################################
# VALIDATION
timeout_seconds: 10
check_pods: 
  - name: hello-world-{{ uuid }}
    namespace: {{ namespace }}

check_logs: 
  - name: hello-world-{{ uuid }}
    namespace: {{ namespace }}
    container: hello-world
    regex: hello world
    operator: Exists
      
clean_configs:
  - type: pod
    name: hello-world-{{ uuid }}
    namespace: {{ namespace }}
    condition: always

```



