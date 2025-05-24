from datetime import datetime
import json
import logging
import requests
from requests.auth import HTTPBasicAuth

from integrations.processor import Processor

logger = logging.getLogger(__name__)


class JenkinsAPIProcessor(Processor):
    def __init__(self, url, username, api_token=None, crumb=False):
        self.config = {
            'url': url
        }
        self.username = username
        self.api_token = api_token
        self.crumb_enabled = crumb
        self.crumb = None
        self.crumb_header = None

        # For API token auth
        if not self.crumb_enabled:
            if not api_token:
                raise Exception("API Token is required when not using crumb authentication")
            self.auth = HTTPBasicAuth(username, api_token)
        else:
            # For crumb-based auth, we'll still use basic auth with username
            self.auth = HTTPBasicAuth(username, api_token if api_token else "")

    def _make_request(self, method, url, **kwargs):
        """
        Helper method to make HTTP requests with proper authentication
        """
        try:
            headers = kwargs.pop('headers', {})

            # Add crumb header if using crumb authentication
            if self.crumb_enabled:
                if not self.crumb:
                    self.fetch_crumb()
                if self.crumb and self.crumb_header:
                    headers[self.crumb_header] = self.crumb
            kwargs['headers'] = headers
            kwargs['auth'] = self.auth
            response = requests.request(method, url, **kwargs)

            # Handle crumb expiration
            if response.status_code == 403 and self.crumb_enabled:
                # Refresh crumb and retry once
                self.crumb = None
                self.fetch_crumb()
                if self.crumb and self.crumb_header:
                    headers[self.crumb_header] = self.crumb
                    kwargs['headers'] = headers
                    response = requests.request(method, url, **kwargs)

            return response
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise e

    def test_connection(self):
        try:
            url = f"{self.config['url']}/api/json"
            response = self._make_request('GET', url)

            if response.status_code == 200:
                return True
            else:
                return Exception(f"Connection failed: {response.status_code}, {response.text}")
        except Exception as e:
            logger.error(f"Exception occurred while testing Jenkins connection with error: {e}")
            raise e

    def fetch_crumb(self):
        """
        Fetch the Jenkins crumb for CSRF protection.
        """
        try:
            url = f"{self.config['url']}/crumbIssuer/api/json"
            # Use direct request here to avoid recursive _make_request call
            response = requests.get(url, auth=self.auth)

            if response.status_code == 200:
                crumb_data = response.json()
                self.crumb = crumb_data.get("crumb")
                self.crumb_header = crumb_data.get("crumbRequestField")
                return self.crumb
            else:
                logger.error(f"Failed to fetch Jenkins crumb: {response.status_code}, {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error fetching crumb: {e}")
            return None

    def run_job(self, job_name, parameters=None, timeout=120):
        """
        Trigger a Jenkins job build.
        Args:
            job_name: Full path of the job to run (e.g., folder/job or nested/folder/job)
            parameters: Optional dictionary of build parameters
            timeout: Request timeout in seconds
        """
        try:
            # Construct the job path URL properly
            path_segments = job_name.split('/')
            url_path = ""
            for segment in path_segments:
                if segment:  # Skip empty segments
                    url_path += f"/job/{requests.utils.quote(segment)}"
            
            # Construct URL based on whether parameters are provided
            if parameters and isinstance(parameters, dict) and parameters:  # Check if parameters is a non-empty dict
                url = f"{self.config['url']}{url_path}/buildWithParameters"
                response = self._make_request('POST', url, data=parameters, timeout=timeout)
            else:
                url = f"{self.config['url']}{url_path}/build?delay=0sec"
                response = self._make_request('POST', url, data='', timeout=timeout)
            
            if response.status_code == 201:
                return True
            else:
                raise Exception(f"Failed to trigger job build: {response.status_code}, {response.text}")
        except Exception as e:
            logger.error(f"Exception occurred while triggering Jenkins job with error: {e}")
            raise e

    def get_all_jobs_recursive(self, folder_path="", timeout=120, depth=0, max_depth=10):
        """
        Recursively get all jobs, including those in folders.
        
        Args:
            folder_path: The path to the folder (empty for root)
            timeout: Request timeout in seconds
            depth: Current recursion depth (used internally)
            max_depth: Maximum recursion depth to prevent infinite loops
            
        Returns:
            List of jobs with their full paths and metadata
        """
        # Guard against too much recursion
        if depth > max_depth:
            print(f"Maximum recursion depth reached at {folder_path}. Stopping recursion.", flush=True)
            return []
        try:
            # Build the URL based on whether we're checking root or a folder
            if folder_path:
                # For folder paths, construct the URL properly with /job/ between each component
                path_segments = folder_path.split('/')
                url_path = ""
                for segment in path_segments:
                    if segment:  # Skip empty segments
                        url_path += f"/job/{requests.utils.quote(segment)}"
                
                url = f"{self.config['url']}{url_path}/api/json?tree=jobs[name,url,_class]"
                print(f"Fetching jobs from: {url}", flush=True)
            else:
                url = f"{self.config['url']}/api/json?tree=jobs[name,url,_class]"
                
            response = self._make_request('GET', url, timeout=timeout)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch Jenkins jobs: {response.status_code}, {response.text}")
                return []
                
            data = response.json()
            jobs = data.get('jobs', [])
            result = []
            
            for job in jobs:
                job_name = job.get("name", "")
                job_class = job.get("_class", "")
                
                # Build the full path for this job
                full_path = f"{folder_path}/{job_name}" if folder_path else job_name
                
                # Add this job to our result list
                result.append({
                    "name": job_name,
                    "class": job_class,
                    "full_path": full_path
                })
                
                # If this is a folder, recursively get its jobs
                if "folder" in job_class.lower() or "directory" in job_class.lower():
                    print(f"Found folder: {full_path}", flush=True)
                    # Add a debug print to help with troubleshooting
                    nested_jobs = self.get_all_jobs_recursive(full_path, timeout, depth=depth+1, max_depth=max_depth)
                    if nested_jobs:
                        print(f"Found {len(nested_jobs)} nested jobs in {full_path}", flush=True)
                    else:
                        print(f"No nested jobs found in {full_path}", flush=True)
                    result.extend(nested_jobs)
                    
            return result
        except Exception as e:
            logger.error(f"Error fetching jobs recursively: {e}")
            return []
    
    def get_job_parameters(self, job_name, timeout=120):
        """Get parameters for a specific job.
        
        Args:
            job_name: Full path of the job (e.g., folder/job or nested/folder/job)
            timeout: Request timeout in seconds
            
        Returns:
            List of parameter definitions with name, type, default value, etc.
        """
        try:
            # Construct the job path URL properly
            path_segments = job_name.split('/')
            url_path = ""
            for segment in path_segments:
                if segment:  # Skip empty segments
                    url_path += f"/job/{requests.utils.quote(segment)}"
                    
            url = f"{self.config['url']}{url_path}/api/json"
            response = self._make_request('GET', url, timeout=timeout)

            if response.status_code == 200:
                data = response.json()
                property_list = data.get('property', [])
                for prop in property_list:
                    if 'parameterDefinitions' in prop:
                        return prop['parameterDefinitions']
                return []  # No parameters found
            else:
                logger.error(f"Failed to get job parameters: {response.status_code}, {response.text}")
                return []
        except Exception as e:
            logger.error(f"Exception occurred while getting job parameters with error: {e}")
            return []

    def get_last_build(self, job_name, timeout=120):
        """Get the last build details for a job.
        
        Args:
            job_name: Full path of the job (e.g., folder/job or nested/folder/job)
            timeout: Request timeout in seconds
            
        Returns:
            List of build details
        """
        try:
            # Construct the job path URL properly
            path_segments = job_name.split('/')
            url_path = ""
            for segment in path_segments:
                if segment:  # Skip empty segments
                    url_path += f"/job/{requests.utils.quote(segment)}"
                    
            url = f"{self.config['url']}{url_path}/lastBuild/api/json"
            response = self._make_request('GET', url, timeout=timeout)
            result = []
            if response.status_code == 200:
                data = response.json()
                build_time = data.get('timestamp')
                number = data.get('number', None)
                status = data.get('result', None)
                actions = data.get('actions', [])
                build_parameters = {}
                for action in actions:
                    if 'parameters' in action:
                        for param in action['parameters']:
                            if 'name' in param and 'value' in param:
                                build_parameters[param['name']] = param['value']
                            elif 'name' in param:
                                build_parameters[param['name']] = None
                logs = ""
                logs_url = f"{self.config['url']}{url_path}/{number}/consoleText"
                logs_response = self._make_request('GET', logs_url, timeout=timeout)
                if logs_response.status_code == 200:
                    logs = logs_response.text
                result.append({
                    'Time': datetime.fromtimestamp(build_time / 1000.0).strftime('%Y-%m-%d %H:%M:%S'),
                    'Build #': number,
                    'Status': status,
                    'Parameters': json.dumps(build_parameters, indent=2),
                    'Logs': logs
                })
            else:
                logger.error(f"Failed to fetch Jenkins last build: {response.status_code}, {response.text}")
                raise Exception(f"Failed to fetch Jenkins last build: {response.status_code}, {response.text}")
            return result
        except Exception as e:
            logger.error(f"Exception occurred while fetching Jenkins last build with error: {e}")
            raise e
