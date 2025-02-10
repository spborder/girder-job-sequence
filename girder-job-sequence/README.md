# girder-job-sequence

This is a utility package for running multiple Girder jobs in a sequence.

- Define a group of jobs with inputs:
    - Only pass non-default parameters
    - Use wildcard "{{}}" strings to define inputs that are not present until they are created with a previous plugin
```python

# This is where you define which plugins you'd like to run and in what order

```
- Check default parameters with:

```python
# Code example showing how to get default plugin parameters

```
- Add a new plugin to a specific instance
- Check status of group of jobs
- Set email notification for job step or group




