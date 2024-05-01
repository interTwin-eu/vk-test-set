from typing import List, Dict, Literal, Any

from pydantic import BaseModel, Extra, Field
import yaml

TemplateKey = Literal[
    'annotations', 
    'namespace', 
    'tolerations',
]

class ConfigManager (BaseModel, extra='forbid'):
   required_namespaces: List[str] = Field([])
   target_nodes: List[str] = Field([])
   values: Dict[TemplateKey, Any]

   @staticmethod
   def from_yaml(config_filename: str):
      with open(config_filename) as input_file:
          return ConfigManager(**yaml.safe_load(input_file.read()))

      
