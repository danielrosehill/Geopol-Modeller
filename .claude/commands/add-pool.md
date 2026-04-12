Add a new model pool to config/pools.yaml.

$ARGUMENTS should be in the format: pool-name planner-model player-model

Steps:
1. Read the current config/pools.yaml
2. Parse the arguments: first word is pool name, second is planner model ID, third is player model ID
3. Add the new pool entry following the existing format
4. Validate that the YAML is still valid
5. Report the new pool configuration
