import os, os.path
import re
import uuid
from tempfile import NamedTemporaryFile
from glob import glob
from itertools import product as cross

import pytest
from jinja2 import Environment, FileSystemLoader
from kubernetes.utils import create_from_yaml
import yaml

from vktestset import kubernetes_api, ConfigManager, ValidationProcedure

cfg = ConfigManager.from_yaml(os.environ.get("VKTEST_CONFIG", "vktest_config.yaml"))
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = sorted([os.path.basename(f) for f in glob(os.path.join(TEMPLATES_DIR, "*.yaml"))])

@pytest.mark.parametrize("namespace", cfg.required_namespaces)
def test_namespace_exists(namespace):
    with kubernetes_api() as k8s:
      assert namespace in [ns.metadata.name for ns in k8s.list_namespace().items], \
             f"Required namespace `{namespace}` is not present."


@pytest.mark.parametrize("node", cfg.target_nodes)
def test_node_exists(node):
    with kubernetes_api() as k8s:
      assert node in [n.metadata.name for n in k8s.list_node().items]


def split_manifest_and_validation(template_filename):
    lines = template_filename.split("\n")
    validation_header = [len(re.findall(r"\#+ *validation", s.lower())) > 0 for s in lines]
    if any(validation_header):
        index = validation_header.index(True)
        return (
            "\n".join(lines[:index]), 
            ValidationProcedure.from_dict(yaml.safe_load("\n".join(lines[index:])))
            )

    return "\n".join(lines), ValidationProcedure()


@pytest.mark.parametrize("node,template", cross(cfg.target_nodes, templates))
def test_manifest(node, template):
    manifest, validation = split_manifest_and_validation(
      Environment(loader=FileSystemLoader(TEMPLATES_DIR))
      .get_template(template)
      .render(dict(**cfg.values, target_node=node, uuid=uuid.uuid4()))
    )

    print (manifest)
    print (validation)

    with kubernetes_api("api_client") as k8s:
        with NamedTemporaryFile(mode='w+', suffix='.yaml') as f:
            f.write(manifest)
            f.seek(0)
            create_from_yaml(k8s, f.name)
  
    validation.execute(timeout_multiplier=cfg.timeout_multiplier)     

