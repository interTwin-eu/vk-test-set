import time
import re
from pprint import pformat
from datetime import datetime
from typing import List, Literal, Optional, Mapping, Any, Union

from pydantic import BaseModel, Field
from vktestset import kubernetes_api

class RecoverableError(RuntimeError):
    "An error time can fix, will wait timeout before giving up"
    pass

class TestFailure(RuntimeError):
    "An error indicating the test has failed. Give up immediately."
    def __init__(self, title, desc=""):
        RuntimeError.__init__(self, title)
        self.description = desc

    def __str__(self):
        return f"""{RuntimeError.__str__(self)}

        {self.description}
        """

PodStatus = Literal[
    'Pending', 
    'Running', 
    'Succeeded', 
    'Failed', 
    'Unknown', 
    ] 

Cleanable = Literal[
    'pod',
    'namespace',
    'service',
    'config_map',
    'secret',
    ]

CleanupCondition = Literal[
    'always',
    'never',
    'onSuccess',
    'onFailure',
    ]

RegexOperator = Literal[
    'Exists',
    'CountAtLeast',
    'CountAtMost',
    'CountExactly',
    'Is'
    ]


    

class CheckPod(BaseModel, extra='forbid'):
    name: str
    namespace: str
    status: PodStatus = 'Succeeded'

    def execute(self, k8s):
        pod = k8s.read_namespaced_pod(name=self.name, namespace=self.namespace)
        if self.status != "Failed" and pod.status.phase == "Failed":
            raise TestFailure(f"Pod {self.name}.{self.namespace} failed", str(pod))
        if pod.status.phase != self.status:
            raise RecoverableError()


class CheckLogs(BaseModel, extra='forbid'):
    name: str
    namespace: str
    regex: str
    operator: RegexOperator = 'Exists'
    container: Optional[str] = None
    value: Optional[Union[str, int]] = None

    def execute(self, k8s):    
        log = k8s.read_namespaced_pod_log(self.name, self.namespace, container=self.container)
        matches = re.findall(self.regex, log)
        print (matches)
        if self.operator in ['Exists'] and len(matches) <= 0: 
            raise RecoverableError(f"Expression {self.regex} does not match log: \n{log}")
        if self.operator in ['CountAtLeast', 'CountExactly'] and len(matches) < int(self.value): 
            raise RecoverableError(f"Expression {self.regex} not sufficiently repeated in log \n{log}")
        if self.operator in ['CountAtMost', 'CountExactly'] and len(matches) > int(self.value): 
            raise TestFailure(f"Found too many occurrencies of {self.regex}", log)
        if self.operator in ['Is'] and str(self.value) not in matches:
            raise RecoverableError(f"Expression {self.regex} returned matches: {matches}. {self.value} expected.\n{log}")



class CleanConfig(BaseModel, extra='forbid'):
    type: Cleanable
    name: str
    namespace: Optional[str] = None
    condition: CleanupCondition = 'always'

    def execute(self, k8s, succeeded: bool):
        clean_after_success = succeeded and self.condition in ['always', 'onSuccess']
        clean_after_failure = not succeeded and self.condition in ['always', 'onFailure']

        if clean_after_success or clean_after_failure:
            if self.type in ['namespace']:
                getattr(k8s, f"delete_{self.type}")(self.name)
            elif self.type in ['pod', 'service', 'config_map', 'secret']:
                getattr(k8s, f"delete_namespaced_{self.type}")(self.name, self.namespace)


class ValidationProcedure(BaseModel, extra='forbid'):
    timeout_seconds: float = 60.
    clean_configs: List[CleanConfig] = Field([])
    check_pods: List[CheckPod] = Field([])
    check_logs: List[CheckLogs] = Field([])

    @staticmethod
    def from_dict(dictionary: Optional[Mapping[str, Any]] = None):
        if dictionary is None:
            return ValidationProcedure()
        
        return ValidationProcedure(**dictionary)

    def execute(self):
        start_time = datetime.now()
        succeeded = False
        try:
            while (datetime.now() - start_time).total_seconds() < self.timeout_seconds:
                try:
                    with kubernetes_api() as k8s:
                        for check_pod in self.check_pods:
                            check_pod.execute(k8s)
                        for check_logs in self.check_logs:
                            check_logs.execute(k8s)

                except RecoverableError:
                    time.sleep(1) 

                else:
                    succeeded = True
                    break
                
        finally:
            with kubernetes_api() as k8s:
                for cleanup in self.clean_configs:
                    cleanup.execute(k8s, succeeded=succeeded)

        if not succeeded: 
            raise TimeoutError(f"Validation failed after {self.timeout_seconds} seconds")


    

