"""Defining Sequence class
"""

from typing_extensions import Union
import requests
from time import sleep

from .utils import get_unique_id

class Sequence:
    """Base class of Sequence, containing multiple jobs
    """
    def __init__(self,
                 gc,
                 jobs: list = []):
        
        self.gc = gc
        self.jobs = jobs
        self.id = get_unique_id()

    def get_logs(self, type = 'all'):
        
        assert type in ['all','running','finished']
        
        current_job_statuses = self.get_status()

        logs_list = []
        if type=='all':
            for j,status in zip(self.jobs,current_job_statuses):
                if status not in ['INACTIVE','QUEUED']:
                    logs_list.append(
                        {
                            'Job Name': j.executable_dict.title,
                            'Logs': j.get_logs()
                        }
                    )
        elif type=='running':
            for j,status in zip(self.jobs,current_job_statuses):
                if status=='RUNNING':
                    logs_list.append(
                        {
                            'Job Name': j.executable_dict.title,
                            'Logs': j.get_logs()
                        }
                    )
        
        elif type == 'finished':
            for j,status in zip(self.jobs,current_job_statuses):
                if status in ['SUCCESS','ERROR','CANCELED']:
                    logs_list.append(
                        {
                            'Job Name': j.executable_dict.title,
                            'Logs': j.get_logs()
                        }
                    )

        return logs_list

    def get_status(self)->list:
        """Get the statuses of all jobs in a sequence

        :return: List of {'Job Name': '', 'Status': ''} dictionaries
        :rtype: list
        """
        status_list = []
        for j in self.jobs:
            status_list.append(
                {'Job Name': j.executable_dict["title"], 'Status': j.get_status()}
            )

        return status_list

    def cancel(self, type:str = 'all')->list:
        """Cancel either all, running, queued, or inactive jobs in a sequence

        :param type: str, defaults to 'all'
        :type type: str, optional
        :return: Either a list (if multiple jobs are canceled) or a single dictionary with the cancellation response
        :rtype: list
        """

        assert type in ['all','running','queued','inactive']
        
        cancel_responses = []
        current_job_statuses = self.get_status()
        if type =='all':
            for j,status in zip(self.jobs,current_job_statuses):
                if not status in ['SUCCESS','ERROR','CANCELED']:
                    cancel_responses.append(j.cancel())
        
        else:
            for j,status in zip(self.jobs,current_job_statuses):
                if status==type.upper():
                    cancel_responses.append(j.cancel())

        return cancel_responses

    def add_sequence_metadata(self, job, job_idx):

        # This might not actually be possible to add
        put_response = self.gc.put(
            f'/job/{job.job_id}/metadata',
            data = {
                'part_of': self.id,
                'preceded_by': self.jobs[job_idx-1].job_id if job_idx>0 else '',
                'followed_by': self.jobs[job_idx+1].plugin_id if len(self.jobs)>job_idx+1 else ''
            }
        )

        return put_response

    def start(self, check_interval:int = 5, cancel_on_error:bool = True,verbose:bool = False):
        """Start the job sequence, checking the status of running jobs every "check_interval" seconds

        :param check_interval: How many seconds to go between status checks, defaults to 5
        :type check_interval: int, optional
        :param cancel_on_error: Whether to cancel the whole job sequence if one of the jobs fails, defaults to True
        :type cancel_on_error: bool, optional
        :param verbose: Whether to print current job and status at each check
        :type verbose: bool, optional
        """

        assert check_interval>0

        for job_idx, job in enumerate(self.jobs):

            job_request = job.start()
            if job_request.status_code==200:
                #job_info = job_request.json()
                current_status = job.get_status()
                #self.add_sequence_metadata(job,job_idx)

                while not current_status in ['SUCCESS','ERROR','CANCELED']:
                    sleep(check_interval)

                    current_status = job.get_status()

                    if verbose:
                        print('-------------------------')
                        print(f'On {job.executable_dict["title"]}, Status: {current_status}')
                        print('-------------------------')


                    if current_status in ['ERROR','CANCELED']:
                        
                        if verbose:
                            print('XXXXXXXXXXXXXXXXXXXXXXXXXXXX')
                            print(f'{current_status} encountered on job: {job.job_id}, {job.executable_dict["title"]}')
                            print('XXXXXXXXXXXXXXXXXXXXXXXXXXXX')

                        if cancel_on_error:
                            if verbose:
                                print('Canceling remaining jobs in sequence')

                            self.cancel()
                            break
            else:

                print('Error submitting job request')
                print(f'Status Code: {job_request.status_code}')
                print(job_request.content)

                if cancel_on_error:
                    self.cancel()
                    break







