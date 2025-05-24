import logging
from copy import deepcopy

from integrations.source_api_processors.jenkins_api_processor import JenkinsAPIProcessor
from integrations.source_metadata_extractor import SourceMetadataExtractor
from protos.base_pb2 import Source, SourceModelType
from utils.logging_utils import log_function_call

logger = logging.getLogger(__name__)


class JenkinsSourceMetadataExtractor(SourceMetadataExtractor):

    def __init__(self, request_id: str, connector_name: str, url: str, username: str, api_token: str,
                 crumb: bool = False, ):
        self.jenkins_processor = JenkinsAPIProcessor(url, username, api_token, crumb=crumb)
        super().__init__(request_id, connector_name, Source.ARGOCD)

    @log_function_call
    def extract_jobs(self):
        model_data = {}
        model_type = SourceModelType.JENKINS_JOBS
        try:
            jobs_response = self.jenkins_processor.test_connection()
            if jobs_response is not True:
                logger.error("Jenkins connection test failed.")
                return model_data

            # Get all jobs recursively (including those in folders)
            all_jobs = self.jenkins_processor.get_all_jobs_recursive()
            
            if not all_jobs:
                logger.error("No jobs found or error occurred while fetching jobs.")
                return model_data

            print(f"Found {len(all_jobs)} total Jenkins jobs/folders", flush=True)
            
            # Process jobs in groups by path depth to ensure parent folders are processed first
            # Group jobs by their depth in the folder hierarchy
            jobs_by_depth = {}
            for job in all_jobs:
                job_full_path = job.get("full_path", "")
                depth = len(job_full_path.split('/')) - 1
                if depth not in jobs_by_depth:
                    jobs_by_depth[depth] = []
                jobs_by_depth[depth].append(job)
            
            # Process jobs in order from shallowest to deepest
            for depth in sorted(jobs_by_depth.keys()):
                jobs_at_depth = jobs_by_depth[depth]
                print(f"Processing {len(jobs_at_depth)} items at depth {depth}", flush=True)
                
                for job in jobs_at_depth:
                    try:
                        job_name = job.get("name", "")
                        job_class = job.get("class", "")
                        job_full_path = job.get("full_path", "")
                        
                        is_folder = "folder" in job_class.lower() or "directory" in job_class.lower()
                        
                        if job_full_path:
                            # Get parameters for this job (only for non-folders)
                            parameters = [] if is_folder else self.jenkins_processor.get_job_parameters(job_full_path)
                            
                            # Use full_path as the unique identifier, but keep the simple name
                            model_data[job_full_path] = {
                                "name": job_name,
                                "full_path": job_full_path,
                                "class": job_class,
                                "parameters": parameters
                            }
                    except KeyError as e:
                        logger.error(f"Missing key {e} in job: {job}")
        except Exception as e:
            logger.error(f'Error extracting Jenkins jobs: {e}')

        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)

