import logging

from integrations.source_metadata_extractor import SourceMetadataExtractor
from integrations.source_api_processors.github_api_processor import GithubAPIProcessor
from protos.base_pb2 import Source, SourceModelType
from utils.logging_utils import log_function_call

logger = logging.getLogger(__name__)


class GithubSourceMetadataExtractor(SourceMetadataExtractor):

    def __init__(self, request_id, connector_name, api_key, org):
        self.org = org
        self.gh_processor = GithubAPIProcessor(api_key, org)
        super().__init__(request_id, connector_name, Source.GITHUB)

    @log_function_call
    def extract_repos(self):
        model_data = {}
        model_type = SourceModelType.GITHUB_REPOSITORY

        try:
            repos = self.gh_processor.list_all_repos()
            if not repos:
                return model_data
            for repo in repos:
                model_data[repo['name']] = repo
        except Exception as e:
            logger.error(f'Error extracting Github repositories: {e}')
        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)

    @log_function_call
    def extract_members(self):
        model_data = {}
        model_type = SourceModelType.GITHUB_MEMBER

        try:
            members = self.gh_processor.list_all_members()
            if not members:
                return model_data
            for member in members:
                model_data[member['login']] = member
        except Exception as e:
            logger.error(f'Error extracting Github members: {e}')
        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)
