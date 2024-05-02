# ValidationProcedure

*Defines the procedure to evaluate whether a test is successful.*

## Properties

- **`timeout_seconds`** *(number)*
- **`clean_configs`** *(array)*: List of operation defining the clean-up procedure. Default: `[]`.
  - **Items**: Refer to *[#/$defs/CleanConfig](#%24defs/CleanConfig)*.
- **`check_pods`** *(array)*: List of checks on the pod status. Default: `[]`.
  - **Items**: Refer to *[#/$defs/CheckPod](#%24defs/CheckPod)*.
- **`check_logs`** *(array)*: List of checks on the logs of pods. Default: `[]`.
  - **Items**: Refer to *[#/$defs/CheckLogs](#%24defs/CheckLogs)*.
## Definitions

- <a id="%24defs/CheckLogs"></a>**`CheckLogs`** *(object)*: Descrive a test on the logs. Cannot contain additional properties.
  - **`name`** *(string, required)*: Name of the Pod.
  - **`namespace`** *(string, required)*: Namespace where the Pod is defined.
  - **`regex`** *(string, required)*: Regular expression to be applied to the log.
  - **`operator`** *(string)*: Operation to be applied on the output of the regular expression. Must be one of: `["Exists", "CountAtLeast", "CountAtMost", "CountExactly", "Is"]`. Default: `"Exists"`.
  - **`container`**: Name of the container. Mandatory for multi-container pods. Default: `null`.
    - **Any of**
      - *string*
      - *null*
  - **`value`**: Value to check the result of the regex agains. Optional for `Exists` operator. Default: `null`.
    - **Any of**
      - *string*
      - *integer*
      - *null*
- <a id="%24defs/CheckPod"></a>**`CheckPod`** *(object)*: Describe a test on the status of a pod or of its containers. Cannot contain additional properties.
  - **`name`** *(string, required)*: Name of the Pod.
  - **`namespace`** *(string, required)*: Namespace where the Pod is defined.
  - **`status`** *(string)*: Status of the pod for the test to succeed. Must be one of: `["Pending", "Running", "Succeeded", "Failed", "Unknown"]`. Default: `"Succeeded"`.
- <a id="%24defs/CleanConfig"></a>**`CleanConfig`** *(object)*: Define the procedure to clean up things once the test is over. Cannot contain additional properties.
  - **`type`** *(string, required)*: Kubernetes object to delete as part of the clean-up. Must be one of: `["pod", "namespace", "service", "config_map", "secret"]`.
  - **`name`** *(string, required)*: Name of the pod.
  - **`namespace`** *(string, required)*: Namespace where to look for the pod.
  - **`condition`** *(string)*: Condition upon which. Must be one of: `["always", "never", "onSuccess", "onFailure"]`. Default: `"always"`.

