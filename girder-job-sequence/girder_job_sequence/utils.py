"""Utility functions used by girder-job-sequence
"""

import os
from typing_extensions import Union
import json

from uuid import uuid4

def get_unique_id():
    """Create a unique id for something"""
    return uuid4().hex[:24]

def id_from_info(gc, docker_image_name: str, cli_name: str):
    """Find a plugin's info from the name of the Docker image (image/name:tag) and CLI name

    :param gc: Girder client handler
    :type gc: None
    :param docker_image_name: Name of the Docker image that has that CLI (image/name:tag)
    :type docker_image_name: str
    :param cli_name: Name of the CLI
    :type cli_name: str
    """

    plugin_list = gc.get('/slicer_cli_web/cli')

    plugin_info = None
    for p in plugin_list:
        if p['image']==docker_image_name and p['name']==cli_name:
            plugin_info = p
            break

    return plugin_info

def get_text_key_vals(xml_dict:dict):
    """Used for grabbing ".text" of values in dictionary containing XML sub-elements

    :param xml_dict: Dictionary containing keys and values with the "text" method or None
    :type xml_dict: dict
    :return: Same dictionary but with XML values replaced with their "text"
    :rtype: dict
    """
    return_dict = xml_dict.copy()
    for key,val in return_dict.items():
        if not val is None:
            try:
                return_dict[key] = val.text
            except:
                return_dict[key] = val
    
    return return_dict

def find_item(gc,type: str, query:str):

    if type=='path':
        item_info = gc.get(f'/resource/lookup',parameters={'path': query})['_id']
    elif type=='_id':
        item_info = gc.get(f'/item/{query}')['_id']

    return item_info

def find_file(gc, item_type:str, item_query:str, file_type:str, file_query:str):

    if item_type == 'path':
        item_info = find_item(gc,item_type, item_query)
    elif item_type=='_id':
        item_info = item_query
    
    if file_type == 'fileName':
        item_files = gc.get(f'/item/{item_info}/files',parameters = {'limit': 0})

        file_names = [i['name'] for i in item_files]
        file_info = item_files[file_names.index(file_query)]['_id']
    
    elif file_type == '_id':
        file_info = file_query

    return file_info

def find_annotation(gc, item_type, item_query, annotation_type, annotation_query):

    if item_type=='path': 
        item_info = find_item(gc, item_type,item_query)
    elif item_type == '_id':
        item_info = item_query

    if annotation_type == 'annotationName':
        item_annotations = gc.get(f'/annotation',parameters={'itemId': item_info["_id"]})

        annotation_names = [i['annotation']['name'] for i in item_annotations]
        annotation_info = item_annotations[annotation_names.index(annotation_query)]['_id']
    elif annotation_type=='annotationId':
        annotation_info = annotation_query

    return annotation_info

def check_wildcard(test_str: str):
    """Check whether a string is a candidate for wildcard input

    :param test_str: String value to test
    :type test_str: str
    """
    return '{{' in test_str

def parse_wildcard(gc, wildcard_str:str):
    """Parse wildcard input, using type, {item,file,or annotation}_type and {item,file,or annotation}_query key-val pairs to search for items, files, or annotations

    :param gc: Girder client handler
    :type gc: None
    :param wildcard_str: String containing "{{}}" wildcard indicator
    :type wildcard_str: str
    """
    # Verifying this is a wildcard candidate
    assert '{{' in wildcard_str
    wildcard_args = json.loads(wildcard_str[1:-1].replace("'",'"'))

    if wildcard_args['type']=='item':
        wildcard_val = find_item(gc, wildcard_args['item_type'], wildcard_args['item_query'])
    elif wildcard_args['type']=='folder':
        # This is the same function since they both use the /resource/lookup endpoint for path types
        wildcard_val = find_item(gc,wildcard_args['folder_type'],wildcard_args['folder_query'])
    elif wildcard_args['type']=='file':
        wildcard_val = find_file(gc, wildcard_args['item_type'],wildcard_args['item_query'],wildcard_args['file_type'],wildcard_args['file_query'])
    elif wildcard_args['type']=='annotation':
        wildcard_val = find_annotation(gc,wildcard_args['item_type'],wildcard_args['item_query'],wildcard_args['annotation_type'],wildcard_args['anotation_query'])

    return wildcard_val

def from_json(gc, json_path: str):
    """Read job or job sequence from JSON file

    :param gc: Girder client handler
    :type gc: None
    :param json_path: Path to json file containing data
    :type json_path: str
    """

    assert os.path.exists(json_path)

    with open(json_path,'r') as f:
        job_json = json.load(f)

        f.close()
    
    if type(job_json)==dict:
        job_json = [job_json]
    
    job_list = from_list(job_json)
    
    return job_list

def from_dict(gc, dict_data:dict):
    """Method for creating job/sequence from a dictionary

    :param gc: Girder client handler
    :type gc: None
    :param dict_data: _description_
    :type dict_data: dict
    """
    from .job import Job

    job_from_dict = Job(
        gc = gc,
        plugin_id = dict_data['plugin_id'] if 'plugin_id' in dict_data else None,
        docker_image=dict_data['docker_image'] if 'docker_image' in dict_data else None,
        cli= dict_data['cli'] if 'cli' in dict_data else None,
        input_args = dict_data['input_args'] if 'input_args' in dict_data else None
    )

    return job_from_dict

def from_list(gc, list_data:list):
    """Generating job/sequence from list of dictionaries

    :param list_data: _description_
    :type list_data: list
    """

    job_list = []
    for l in list_data:
        job_list.append(
            from_dict(gc,l)
        )

    if len(job_list)>1:
        from .sequence import Sequence
        return Sequence(gc,job_list)
    else:
        return job_list[0]





