# girder-job-sequence

This is a utility package for running multiple Girder jobs in a sequence.

- Define a group of jobs with inputs:
    - Only pass non-default parameters
    - Use wildcard "{{}}" strings to define inputs that are not present until they are created with a previous plugin

## Installation
```bash
$ pip install girder-job-sequence
```


## Usage

Here are some of the primary use-cases for this package. Optionally, it can also be run on a background thread.

*Note on wildcard inputs*
```python
# Wildcard inputs let you run plugins in sequence even if one plugin 
# takes an input file that is created as an output of another plugin.
# Here are some examples:

# New item:
# Items have "path" or "_id" types. If the item hasn't been created yet, refer to it by /collection (or /user) path to that item and this will look for it.
item_wildcard = "{{'type':'item', 'item_type': 'path', 'item_query': '/collections/folder/item_name.ndpi'}}"

# Use similar syntax for folders (remove trailing "/")
folder_wildcard = "{{'type':'folder', 'folder_type': 'path', 'folder_query': '/collections/folder'}}"

# New file on an item:
# Files have "fileName" or "_id" types. If the file hasn't been created yet, refer to it using the information you would use to find the "item" that that file is attached to and use the "fileName" type with the name of the file as the "file_query".
file_wildcard = "{{'type': 'file', 'item_type': '_id', 'item_query': 'uuid_string_id', 'file_type': 'fileName', 'file_query': 'output_file.csv'}}"

# Use a similar syntax for new annotations: (make sure these are unique)
annotation_wildcard = "{{'type': 'annotation', 'item_type': '_id', 'item_query': 'uuid_string_id', 'annotation_type': 'annotationName', 'annotation_query': 'Name of Annotation'}}"

# If you want to check the wildcard was filled in correctly, use the following:
from girder_job_sequence.utils import parse_wildcard
from girder_client import GirderClient

gc = GirderClient(apiUrl="http://dsa.address.com/api/v1")

parsed_wildcard_val = parse_wildcard(gc,item_wildcard)
print(parsed_wildcard_val)

```

```python

# This is where you define which plugins you'd like to run and in what order
from girder_job_sequence.utils import from_list

plugin_list = [
    {
        'plugin_id': 'uuid_string',
        'input_args': [
            {
                'name': 'parameter_1',
                'value': 5
            },
            {
                'name': 'parameter_2_with_wildcard',
                'value': "{{'type':'file','item_type':'path','item_query':'/collections/path/to/item.svs','file_type':'fileName','file_query':'name_of_file.csv'}}"
            }
        ]
    },
    {
        'docker_image': 'user/name:tag',
        'cli': 'PluginName',
        'input_args': [
            {
                'name': 'input_param',
                'value': 'blahblahblah'
            }
        ]
    }
]

job_sequence = from_list(job_list)

job_sequence.start(cancel_on_error=True,verbose=True)


```
- Check default parameters with:

```python
# Code example showing how to get default plugin parameters
from girder_job_sequence import Job
import json

job_object = Job(plugin_id = 'uuid_string')

print(json.dumps(job_object.inputs,indent=4))

```

- Check status of group of jobs

```python

from girder_job_sequence.utils import from_list

plugin_list = [
    {
        'plugin_id': 'uuid_string',
        'input_args': [
            {
                'name': 'parameter_1',
                'value': 5
            },
            {
                'name': 'parameter_2_with_wildcard',
                'value': "{{'type':'file','item_type':'path','item_query':'/collections/path/to/item.svs','file_type':'fileName','file_query':'name_of_file.csv'}}"
            }
        ]
    },
    {
        'docker_image': 'user/name:tag',
        'cli': 'PluginName',
        'input_args': [
            {
                'name': 'input_param',
                'value': 'blahblahblah'
            }
        ]
    }
]

job_sequence = from_list(job_list)

job_sequence.start(cancel_on_error=True,verbose=False)

print(job_sequence.get_status())

```

- (#TODO): Set email notification for job step or group

## Contributing

Open to contributions. Feel free to submit a PR or post feature requests in [Issues](https://github.com/spborder/girder-job-sequence/issues)

## Open Projects

- Sending email notifications when a step or a whole job sequence is completed
- Adding conditional functions to decide which job to run following some processing steps.
    - Ex: if a segmentation job has zero of a certain class, cancel the job that depends on that class being present. Or depending on the value of some item metadata, run a different plugin. (This was predicted to be kidney so run the kidney multi-compartment segmentation)

- Various other types of wildcard inputs

- Find some way to PUT metadata to a job on DSA and add provenance information like "this plugin is part_of: 'sequence id', and is preceded_by: 'prev_job_id', and is followed_by: 'next_plugin_id'"

- Integration as girder plugin



## License
`girder-job-sequence` was created by Samuel Border. It is licensed under the terms of the Apache 2.0 License






