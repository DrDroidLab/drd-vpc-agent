import logging
import requests

from integrations.processor import Processor

logger = logging.getLogger(__name__)

class GithubActionsAPIProcessor(Processor):
    def __init__(self, api_key):
        self.__api_key = api_key

    def test_connection(self):
        try:
            url = 'https://api.github.com/octocat'
            headers = {
                'Authorization': f'Bearer {self.__api_key}'
            }
            response = requests.request("GET", url, headers=headers)
            if response.status_code == 200:
                return True
            else:
                raise Exception(f"Connection failed: {response.status_code}, {response.text}")
        except Exception as e:
            logger.error(f"Exception occurred while testing Github connection with error: {e}")
            raise e

    def get_run_info(self, owner, repo, workflow_id):
        try:
            run_url = f'https://api.github.com/repos/{owner}/{repo}/actions/runs/{workflow_id}'
            payload = {}
            headers = {
                'Authorization': f'Bearer {self.__api_key}'
            }
            # Fetch the latest commits for the file
            response = requests.request("GET",run_url, headers=headers,data=payload)
            if response:
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Error occurred while fetching github actions workflow details for workflow: {workflow_id} in {owner}/{repo} "
                                 f"with status_code: {response.status_code} and response: {response.text}")
        except Exception as e:
            logger.error(f"Exception occurred while fetching github actions workflow details "
                         f"for workflow_id: {workflow_id} in {owner}/{repo} with error: {e}")
        return None

    def get_jobs_list(self, owner, repo, workflow_id):
        try:
            job_url = f'https://api.github.com/repos/{owner}/{repo}/actions/runs/{workflow_id}/jobs'
            payload = {}
            headers = {
                'Authorization': f'Bearer {self.__api_key}'
            }
            response = requests.request("GET", job_url, headers=headers, data=payload)
            if response:
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Error occurred while fetching github actions details for workflow_id: {workflow_id} in {owner}/{repo} "
                                 f"with status_code: {response.status_code} and response: {response.text}")
        except Exception as e:
            logger.error(f"Exception occurred while fetching github actions details "
                         f"for workflow_id: {workflow_id} in {owner}/{repo} with error: {e}")
        return None