import logging

from google.protobuf.struct_pb2 import Struct

from utils.credentilal_utils import generate_credentials_dict
from utils.proto_utils import dict_to_proto
from utils.time_utils import format_to_github_timestamp

from google.protobuf.wrappers_pb2 import StringValue

from integrations.source_api_processors.github_api_processor import GithubAPIProcessor
from integrations.source_manager import SourceManager
from protos.base_pb2 import TimeRange, Source, SourceModelType
from protos.connectors.connector_pb2 import Connector as ConnectorProto
from protos.literal_pb2 import LiteralType, Literal
from protos.playbooks.playbook_commons_pb2 import PlaybookTaskResult, PlaybookTaskResultType, ApiResponseResult, \
    TextResult
from protos.playbooks.source_task_definitions.github_task_pb2 import Github
from protos.ui_definition_pb2 import FormField, FormFieldType

logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    pass


class GithubSourceManager(SourceManager):
    def __init__(self):
        self.source = Source.GITHUB
        self.task_proto = Github
        self.task_type_callable_map = {
            Github.TaskType.FETCH_RELATED_COMMITS: {
                'executor': self.fetch_related_commits,
                'model_types': [SourceModelType.GITHUB_REPOSITORY],
                'result_type': PlaybookTaskResultType.API_RESPONSE,
                'display_name': 'Fetch Related Commits for a function',
                'category': 'Code Repository',
                'form_fields': [
                    FormField(key_name=StringValue(value="repo"),
                              display_name=StringValue(value="Repo"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="file_path"),
                              display_name=StringValue(value="Enter File Path"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="function_name"),
                              display_name=StringValue(value="Enter Function name"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="branch"),
                              display_name=StringValue(value="Enter Branch name. Defaults to main"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT,
                              default_value=Literal(type=LiteralType.STRING, string=StringValue(value='main'))),
                ]
            },
            Github.TaskType.FETCH_FILE: {
                'executor': self.fetch_file,
                'model_types': [SourceModelType.GITHUB_REPOSITORY],
                'result_type': PlaybookTaskResultType.API_RESPONSE,
                'display_name': 'Fetch Files',
                'category': 'Code Repository',
                'form_fields': [
                    FormField(key_name=StringValue(value="repo"),
                              display_name=StringValue(value="Enter Repository name"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="file_path"),
                              display_name=StringValue(value="Enter File Name"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                ]
            },
            Github.TaskType.UPDATE_FILE: {
                'executor': self.update_file,
                'model_types': [SourceModelType.GITHUB_REPOSITORY, SourceModelType.GITHUB_MEMBER],
                'result_type': PlaybookTaskResultType.API_RESPONSE,
                'display_name': 'Update Files',
                'category': 'Code Repository',
                'form_fields': [
                    FormField(key_name=StringValue(value="repo"),
                              display_name=StringValue(value="Enter Repository name"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="file_path"),
                              display_name=StringValue(value="Enter File Path"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="file_fetch_button"),
                              display_name=StringValue(value="Fetch File"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.BUTTON_FT),
                    FormField(key_name=StringValue(value="committer_name"),
                              display_name=StringValue(value="Enter Name for Commit message"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="committer_email"),
                              display_name=StringValue(value="Enter Email for Commit message"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="content"),
                              display_name=StringValue(value="Modified Content"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.CODE_EDITOR_FT),
                    FormField(key_name=StringValue(value="sha"),
                              display_name=StringValue(value="Enter Sha of previous commit"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="branch"),
                              display_name=StringValue(value="Enter Branch name. Defaults to main"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT,
                              default_value=Literal(type=LiteralType.STRING, string=StringValue(value='main')),
                              is_optional=True),
                ]
            },
            Github.TaskType.FETCH_RECENT_COMMITS: {
                'executor': self.fetch_recent_commits,
                'model_types': [SourceModelType.GITHUB_REPOSITORY],
                'result_type': PlaybookTaskResultType.API_RESPONSE,
                'display_name': 'Fetch Recent Commits for a branch',
                'category': 'Code Repository',
                'form_fields': [
                    FormField(key_name=StringValue(value="repo"),
                              display_name=StringValue(value="Repo"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="branch"),
                              display_name=StringValue(value="Enter Branch Name. Defaults to main"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT,
                              default_value=Literal(type=LiteralType.STRING, string=StringValue(value='main'))),
                    FormField(key_name=StringValue(value="author"),
                              display_name=StringValue(value="Commit Author (optional)"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT,
                              is_optional=True)
                ]
            },
            Github.TaskType.FETCH_RECENT_MERGES: {
                'executor': self.fetch_recent_merges,
                'model_types': [SourceModelType.GITHUB_REPOSITORY],
                'result_type': PlaybookTaskResultType.API_RESPONSE,
                'display_name': 'Fetch Recent Merges for a branch',
                'category': 'Code Repository',
                'form_fields': [
                    FormField(key_name=StringValue(value="repo"),
                              display_name=StringValue(value="Repo"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TYPING_DROPDOWN_FT),
                    FormField(key_name=StringValue(value="branch"),
                              display_name=StringValue(value="Enter Branch Name. Defaults to main"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT,
                              default_value=Literal(type=LiteralType.STRING, string=StringValue(value='main')))
                ]
            },
        }

    def get_connector_processor(self, github_connector, **kwargs):
        generated_credentials = generate_credentials_dict(github_connector.type, github_connector.keys)
        return GithubAPIProcessor(**generated_credentials)

    def fetch_related_commits(self, time_range: TimeRange, github_task: Github,
                              github_connector: ConnectorProto) -> PlaybookTaskResult:
        try:
            task = github_task.fetch_related_commits
            repo = task.repo.value
            file_path = task.file_path.value
            function_name = task.function_name.value
            branch = task.branch.value
            commits = self.get_connector_processor(github_connector).get_file_commits(repo, file_path, branch)
            if not commits:
                return PlaybookTaskResult(type=PlaybookTaskResultType.TEXT, text=TextResult(output=StringValue(
                    value=f"No commits returned from Github for repo: {repo}, file: {file_path}, branch: {branch} and "
                          f"function: {function_name}")), source=self.source)

            # Loop through the commits and get the diff for each one
            related_commits = []
            for commit in commits:
                commit_sha = commit['sha']
                commit_details = self.get_connector_processor(github_connector).get_commit_sha(repo, commit_sha)
                # Get the diff for the specific file
                for file in commit_details['files']:
                    if file['filename'] == file_path:
                        patch = file.get('patch', '')
                        if function_name in patch:
                            related_commit = {'commit_url': commit['html_url'], 'commit_sha': commit_sha,
                                              'author_name': commit['commit']['author']['name'],
                                              'author_email': commit['commit']['author']['email'],
                                              'commit_date': commit['commit']['author']['date'], 'patch': patch}
                            related_commits.append(related_commit)

            response_struct = dict_to_proto({"all_commits": related_commits}, Struct)
            commit_output = ApiResponseResult(response_body=response_struct)
            return PlaybookTaskResult(type=PlaybookTaskResultType.API_RESPONSE, source=self.source,
                                      api_response=commit_output)
        except Exception as e:
            raise Exception(f"Error while executing Github fetch_related_commits task: {e}")

    def fetch_file(self, time_range: TimeRange, github_task: Github,
                   github_connector: ConnectorProto) -> PlaybookTaskResult:
        try:
            task = github_task.fetch_file
            repo = task.repo.value
            file_path = task.file_path.value
            processor = self.get_connector_processor(github_connector)
            all_repos = processor.list_all_repos()
            all_repo_names = [repo['name'] for repo in all_repos]
            if repo not in all_repo_names:
                raise Exception(f"Repository {repo} not found")
            file_details = processor.fetch_file(repo, file_path)
            response_struct = dict_to_proto(file_details, Struct)
            file_output = ApiResponseResult(response_body=response_struct)
            return PlaybookTaskResult(
                type=PlaybookTaskResultType.API_RESPONSE,
                source=self.source,
                api_response=file_output
            )
        except Exception as e:
            raise Exception(f"Error while executing Github fetch_related_commits task: {e}")

    def update_file(self, time_range: TimeRange, github_task: Github,
                    github_connector: ConnectorProto) -> PlaybookTaskResult:
        try:
            task = github_task.update_file
            repo = task.repo.value
            file_path = task.file_path.value
            content = task.content.value
            sha = task.sha.value
            committer_name = task.committer_name.value
            committer_email = task.committer_email.value
            branch = task.branch.value if task.branch.value else None
            processor = self.get_connector_processor(github_connector)
            all_repos = processor.list_all_repos()
            all_repo_names = [repo['name'] for repo in all_repos]
            if repo not in all_repo_names:
                raise Exception(f"Repository {repo} not found")
            file_details = processor.update_file(repo, file_path, sha, content, committer_name, committer_email,
                                                 branch)
            response_struct = dict_to_proto(file_details, Struct)
            file_output = ApiResponseResult(response_body=response_struct)
            return PlaybookTaskResult(
                type=PlaybookTaskResultType.API_RESPONSE,
                source=self.source,
                api_response=file_output
            )
        except Exception as e:
            raise Exception(f"Error while executing Github fetch_related_commits task: {e}")

    def fetch_recent_commits(self, time_range: TimeRange, github_task: Github,
                             github_connector: ConnectorProto) -> PlaybookTaskResult:
        try:
            task = github_task.fetch_recent_commits
            repo = task.repo.value
            branch = task.branch.value
            time_since = format_to_github_timestamp(time_range.time_geq)
            time_until = format_to_github_timestamp(time_range.time_lt)
            author = task.author.value if task.author.value else None
            recent_commits = self.get_connector_processor(github_connector).get_branch_commits(repo, branch, time_since,
                                                                                               time_until, author)
            response_struct = dict_to_proto({"recent_commits": recent_commits}, Struct)
            commit_output = ApiResponseResult(response_body=response_struct)
            return PlaybookTaskResult(
                type=PlaybookTaskResultType.API_RESPONSE,
                source=self.source,
                api_response=commit_output
            )
        except Exception as e:
            raise Exception(f"Error while executing Github fetch_recent_commits task: {e}")

    def fetch_recent_merges(self, time_range: TimeRange, github_task: Github,
                            github_connector: ConnectorProto) -> PlaybookTaskResult:
        try:
            task = github_task.fetch_recent_merges
            repo = task.repo.value
            branch = task.branch.value
            recent_merges = self.get_connector_processor(github_connector).get_recent_merges(repo, branch)
            response_struct = dict_to_proto({"recent_merges": recent_merges}, Struct)
            commit_output = ApiResponseResult(response_body=response_struct)
            return PlaybookTaskResult(
                type=PlaybookTaskResultType.API_RESPONSE,
                source=self.source,
                api_response=commit_output
            )
        except Exception as e:
            raise Exception(f"Error while executing Github fetch_recent_merges task: {e}")
