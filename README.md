# Virtual Kubelet Test Set 🥚🔨

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

## Configuring the templates

The templates are configured through a YAML file, named by 
default `vktest_config.yaml`.

The fields of the configuration file are:
 * `target_nodes` (*list of strings*), the Kubernetes names of the target nodes to be tested
 * `required_namespaces` (*optional list of strings*), a list of namespace that should exist before other tests are run
 * `timeout_multiplier` (*optional float*), a multiplier for all the timeouts of the test. 
   It can be increased for unattended testing or lowered during debug with cached images on the remote target.
 * `values` (*dictionary*) a dictionary of values passed *as-is* to the jinja2 template

An example of configuration is reported below.

```yaml
target_nodes: 
  - vk-hub-test-agent-1

required_namespaces:
  - default
  - kube-system
  - interlink4

timeout_multiplier: 1.

values:
  namespace: interlink4

  annotations: 
    slurm-job.vk.io/flags: "--job-name=test-pod-cfg -t 2800  --ntasks=8 --nodes=1 --mem-per-cpu=2000"

  tolerations:
    - key: virtual-node.interlink/no-schedule
      operator: Exists
      effect: NoSchedule
```

An implicit variable passed to the jinja template together with the `values` dictionary
is `uuid` which is a random string used to ensure uniquness in 
the names of the created resources.

## Validation structure
The validation section is composed of three dictionaries:
 * `check_pods` defines checks on the status of a pod;
 * `check_logs` defines checks based on regular expressions used to process the log
    of a specified container in a given pod;
 * `clean_configs` defines the clean-up operations to avoid cluttering the cluster
   with completed (or failed) test pods;

In addition, a timeout can be defined specifying the `timeout_seconds` variable.
The tests that wait for some condition to verify to succeed, will not wait longer 
than the specified timeout. 

See the auto-generated documentation in [ValidationProcedure.md](./ValidationProcedure.md).

## Relevant environment variables
 * `KUBECONFIG` points to the configuration file of the connection to the kubernetes 
   cluster (as for [`kubectl`](https://kubernetes.io/docs/reference/kubectl/)). If empty,
   or unset, in-cluster configuration is assumed. 
 * `VKTEST_CONFIG` points to the configuration file of the tests, defaults to 
   `vktest_config.yaml`.

## Running the tests

Make sure you have an active kubectl connection to the cluster where the virtual node 
is configured,
```bash
kubectl get nodes
```
should list the nodes defined in the cluster, including the virtual node.

Clone this repository
```bash
git clone git@github.com:landerlini/vk-test-set.git
cd vk-test-set
```

Configure the tests for your deployment
```bash
vim vktest_config.yaml
```

Run all the tests, with enhanced verbosity (`-v`) and stopping on failure (`-x`).
```bash
pytest -vx
```

Rerun a single test (for example upon failure in the debugging loop) you can 
copy the string identifying the test in the pytest output as an argument of pytest
itself.

For example,
```bash
pytest -v vktestset/basic_test.py::test_manifest[vk-hub-test-agent-1-070-rclone-bind.yaml]
```

### Test order is important
Please note that in the development of tests, features validated by former 
tests are usually assumed, so that related failures might result obfuscated and 
less obvious to identify.

In general, it is a bad idea to test *advanced* features if *basic* features are 
properly working.

## Develop new tests (CONTRIBUTING)

Adding new tests is highly appreciated! 
We encourage contributions both on adding smaller tests that provide early validation
of common pitfalls in the definition of a container plugin and more complex 
tests testing more advanced features. 

In general, if you find a bug in a plugin escaping this test set, we want to know!




