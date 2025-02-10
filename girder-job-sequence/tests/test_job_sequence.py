"""Testing girder-job-sequence
"""

import os
import sys
sys.path.append('.\\girder-job-sequence\\')
from girder_job_sequence import Job, Sequence
from girder_job_sequence.utils import from_list

from girder_client import GirderClient
import json


def main():

    job_list = [
        {
            'plugin_id': '65de6baeadb89a58fea10d4c',
            'input_args': [
                {
                    'name': 'files',
                    'value': '6717e743f433060d2884838c'
                },
                {
                    'name': 'base_dir',
                    'value': '6717e73cf433060d28848389'
                },
                {
                    'name': 'modelfile',
                    'value': '648123761019450486d13dce'
                }
            ]
        },
        {
            'plugin_id': '67a63efdfcdeba1e292f63b3',
            'input_args': [
                {
                    'name': 'input_image',
                    'value': "{{'type':'file','item_type':'path','item_query':'/user/sam123/Public/FUSION_Upload_2024_10_22_13_56_05_219929/XY01_IU-21-015F_001.svs','file_type':'fileName','file_query':'XY01_IU-21-015F_001.svs'}}"
                },
                {
                    'name': 'extract_sub_compartments',
                    'value': True
                },
                {
                    'name': 'hematoxylin_threshold',
                    'value': 150
                },
                {
                    'name': 'eosinophilic_threshold',
                    'value': 30
                },
                {
                    'name': 'hematoxylin_min_size',
                    'value': 40
                },
                {
                    'name': 'eosinophilic_min_size',
                    'value': 20
                },
            ]
        }
    ]

    base_url = 'http://ec2-3-230-122-132.compute-1.amazonaws.com:8080/api/v1'
    gc = GirderClient(
        apiUrl=base_url
    )
    gc.authenticate(
        username = os.environ.get('DSA_USER'),
        password = os.environ.get('DSA_PWORD')
    )

    job_sequence = from_list(gc,job_list)
    print(job_sequence)
    for j in job_sequence.jobs:
        print(json.dumps(j.inputs,indent=4))

    # Running sequence on same thread
    job_sequence.start(verbose = True,cancel_on_error=True)




if __name__=='__main__':
    main()
