"""
Defining Job class
"""
from typing_extensions import Union
import requests

import json
import lxml.etree as ET

from .utils import id_from_info, get_text_key_vals, check_wildcard, parse_wildcard


PARAMETER_TAGS = ['integer','float','double','boolean','string','integer-vector','float-vector','double-vector','string-vector',
                'integer-enumeration','float-enumeration','double-enumeration','string-enumeration','file','directory','image',
                'geometry','point','pointfile','region','table','transform']

JOB_STATUS_KEY = [
    'INACTIVE',
    'QUEUED',
    'RUNNING',
    'SUCCESS',
    'ERROR',
    'CANCELED'
]


class Job:
    """Base class of Job
    """
    def __init__(self,
                 gc,
                 plugin_id:Union[str,None] = None,
                 docker_image: Union[str,None] = None,
                 cli: Union[str,None] = None,
                 input_args: Union[list,None] = None
                 ):
        
        self.gc = gc
        self.plugin_id = plugin_id
        self.docker_image = docker_image
        self.cli = cli
        self.input_args = input_args
        self.job_id = None

        # Either id is defined or both docker_image and cli have to be defined
        assert any([not self.plugin_id is None, all([not j is None for j in [self.docker_image, self.cli]])])

        self.executable_dict = self.get_plugin_info()
        self.inputs = self.parse_input_args()


    def get_plugin_info(self):
        """Finding the plugin in the provided DSA instance either by id or combination of docker_image and cli_name
        """
        executable_dict = None
        if self.plugin_id is None:
            # Already asserted, if self.job_id is None then docker_image and cli have to be defined
            plugin_info = id_from_info(self.gc, self.docker_image, self.cli)

            if not plugin_info is None:
                self.plugin_id = plugin_info['_id']
                executable_dict = self.get_executable()
        else:
            executable_dict = self.get_executable()


        return executable_dict

    def get_executable(self)->dict:
        """Create the executable dictionary for this plugin. Finds plugin descriptive information and organizes inputs in a ready-to-use format.

        :return: Executable dictionary with descriptive information, parameter groups, and each parameter groups inputs
        :rtype: dict
        """
        executable_dict = None
        if not self.plugin_id is None:
            plugin_xml_req = requests.get(
                self.gc.urlBase+f'slicer_cli_web/cli/{self.plugin_id}/xml?token={self.gc.token}'
            )

            if plugin_xml_req.status_code==200:
                plugin_xml = ET.fromstring(plugin_xml_req.content)

                executable_dict = {
                    'title': plugin_xml.find('title'),
                    'description': plugin_xml.find('description'),
                    'author': plugin_xml.find('contributor'),
                    'documentation': plugin_xml.find('documentation-url')
                }

                executable_dict = get_text_key_vals(executable_dict)

                parameters_list = []
                for param in plugin_xml.iterfind('parameters'):
                    param_dict = {
                        'advanced': param.find('advanced'),
                        'label': param.find('label'),
                        'description': param.find('description')
                    }

                    param_dict = get_text_key_vals(param_dict)

                    input_list = []
                    for sub_el in param:
                        if sub_el.tag in PARAMETER_TAGS:
                            input_dict = {
                                'type': sub_el.tag,
                                'label': sub_el.find('label'),
                                'name': sub_el.find('name'),
                                'channel': sub_el.find('channel'),
                                'description': sub_el.find('description'),
                                'default': sub_el.find('default')
                            }
                            input_dict = get_text_key_vals(input_dict)

                            if 'enumeration' in sub_el.tag:
                                options_list = []
                                for opt in sub_el.iterfind('element'):
                                    options_list.append(opt.text)

                                input_dict['options'] = options_list
                        
                            if not sub_el.find('constraints') is None:
                                constraints = sub_el.find('constraints')
                                if not constraints is None:
                                    constraints_dict = {
                                        'min': constraints.find('min'),
                                        'max': constraints.find('max'),
                                        'step': constraints.find('step')
                                    }
                                    constraints_dict = get_text_key_vals(constraints_dict)

                                    input_dict['constraints'] = constraints_dict

                            input_list.append(input_dict)

                    param_dict['inputs'] = input_list

                    parameters_list.append(param_dict)

                executable_dict['parameters'] = parameters_list

            else:
                print(plugin_xml_req.content)

        return executable_dict

    def get_defaults(self)->list:
        """Method for finding all of the default values for the current plugin

        :return: List of {'name': 'default'} or {'label': 'default'} values for each input
        :rtype: list
        """
        defaults_list = []
        if not self.executable_dict is None:
            for p in self.executable_dict['parameters']:
                for i in p['inputs']:
                    defaults_list.append({
                        'name': i['name'],
                        'default': i['default']
                    })

        return defaults_list

    def find_input(self, input_name):

        exe_input = None
        for p in self.executable_dict['parameters']:
            for inp in p['inputs']:
                if inp['name']==input_name:
                    exe_input = inp
                    break
        
        return exe_input

    def parse_input_args(self):
        """Method for organizing user-provided job input values. Only non-default valued inputs are required.
        """

        if not self.input_args is None:
            user_input_names = [i['name'] for i in self.input_args]
            
            for i in self.input_args:
                if type(i['value'])==str:
                    if check_wildcard(i['value']):
                        i['value'] = parse_wildcard(self.gc, i['value'])
        
        else:
            user_input_names = []

        inputs_list = []
        input_names = []
        # Replacing default values
        plugin_defaults = self.get_defaults()
        print(plugin_defaults)
        for p_d in plugin_defaults:
            if 'name' in p_d:
                if p_d['name'] in user_input_names:
                    inputs_list.append({
                        'name': p_d['name'],
                        'value': self.input_args[user_input_names.index(p_d['name'])]['value']
                    })
                else:
                    inputs_list.append({
                        'name': p_d['name'],
                        'value': p_d['default']
                    })
                
                input_names.append(p_d['name'])
            elif 'label' in p_d:
                # This is for non-named inputs which are defined by index
                # Ideally, every input parameter would have a name for reference but some may just have
                # an index.
                inputs_list.append({
                    'name': None,
                    'value': p_d['default']
                })
                input_names.append(p_d['label'])

        # Non-default value-having inputs have to be defined in input_args or they'll be missing
        if not self.input_args is None:
            for i in self.input_args:
                if not i['name'] in input_names:
                    inputs_list.append({
                        'name': i['name'],
                        'value': i['value']
                    })
        
        # Adding girderApiUrl and girderToken
        inputs_list.extend([
            {
                'name': 'girderApiUrl',
                'value': self.gc.urlBase
            },
            {
                'name': 'girderToken',
                'value': self.gc.token
            }
        ])
        input_names.extend(['girderApiUrl','girderToken'])

        # Checking that all inputs are present
        required_inputs = []
        for p in self.executable_dict['parameters']:
            for i in p['inputs']:
                if not i['name'] is None:
                    required_inputs.append(i['name'])
                elif not i['label'] is None:
                    required_inputs.append(i['label'])

        if not all([i in input_names for i in required_inputs]):
            print(f'Missing required inputs')
            for i in required_inputs:
                if not i in input_names:
                    print(f'{i} is missing')
            
            print(f'Provided inputs: {input_names}')


        return inputs_list

    def cancel(self):
        """Send cancel request for this job
        """

        if not self.job_id is None:
            cancel_response = self.gc.put(
                f'/job/{self.job_id}/cancel'
            )

            return cancel_response
        else:
            return {'message': 'Job has not started yet'}

    def start(self):
        """Send start request for this job
        """
        
        start_request = requests.post(
            url = self.gc.urlBase+f'slicer_cli_web/cli/{self.plugin_id}/run?token={self.gc.token}',
            params = {
                i['name']: i['value']
                for i in self.inputs
            }
        )

        if start_request.status_code==200:
            self.job_info = start_request.json()
            self.job_id = self.job_info['_id']

        return start_request

    def get_status(self):
        """Get the status of the current job
        """

        if not self.job_id is None:
            job_info = self.gc.get(f'/job/{self.job_id}')
            job_status_idx = job_info['status']

            return JOB_STATUS_KEY[job_status_idx]
        else:
            return JOB_STATUS_KEY[0]

    def get_logs(self):
        """Get logs of this job
        """

        if not self.job_id is None:
            job_info = self.gc.get(f'/job/{self.job_id}')
            job_logs = job_info['log']

            log_list = [i.split('\n') for i in job_logs]
        else:
            lob_list = ['Job has not started yet']

        return log_list



