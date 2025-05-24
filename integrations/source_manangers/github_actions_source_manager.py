from google.protobuf.struct_pb2 import Struct
from utils.proto_utils import dict_to_proto

from google.protobuf.wrappers_pb2 import StringValue

from integrations.source_api_processors.github_actions_api_processor import GithubActionsAPIProcessor
from integrations.source_manager import SourceManager
from protos.base_pb2 import TimeRange, Source
from protos.literal_pb2 import LiteralType
from protos.connectors.connector_pb2 import Connector as ConnectorProto
from protos.playbooks.playbook_commons_pb2 import PlaybookTaskResult, PlaybookTaskResultType, ApiResponseResult
from protos.playbooks.source_task_definitions.github_actions_task_pb2 import GithubActions
from protos.ui_definition_pb2 import FormField, FormFieldType


from utils.credentilal_utils import generate_credentials_dict

class TimeoutException(Exception):
    pass


class GithubActionsSourceManager(SourceManager):
    def __init__(self):
        self.source = Source.GITHUB_ACTIONS
        self.task_proto = GithubActions
        self.task_type_callable_map = {
            GithubActions.TaskType.FETCH_ACTION_RUN_INFO: {
                'executor': self.fetch_action_run_info,
                'model_types': [],
                'result_type': PlaybookTaskResultType.API_RESPONSE,
                'display_name': 'Fetch Failure reason for a Github Action Run',
                'category': 'CI/CD',
                'form_fields': [
                    FormField(key_name=StringValue(value="owner"),
                              display_name=StringValue(value="Owner"),
                              description=StringValue(value='Enter Owner'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="repo"),
                              display_name=StringValue(value="Repo"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="workflow_id"),
                              display_name=StringValue(value="Enter Run ID"),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                ]
            },
        }
    def get_connector_processor(self, github_actions_connector, **kwargs):
        generated_credentials = generate_credentials_dict(github_actions_connector.type, github_actions_connector.keys)
        return GithubActionsAPIProcessor(**generated_credentials)

    def fetch_action_run_info(self, time_range: TimeRange, github_actions_task: GithubActions,
                              github_actions_connector: ConnectorProto):
        # Loop through the commits and get the diff for each one
        try:
            task = github_actions_task.fetch_action_run_info
            owner = task.owner.value
            repo = task.repo.value
            workflow_id = task.workflow_id.value
            print(f"Fetching action run info for {owner}/{repo}/{workflow_id}")
            runs = self.get_connector_processor(github_actions_connector).get_run_info(owner, repo, workflow_id)
            print(f"Runs: {runs}")
            if runs['status'] == 'failure' or runs['conclusion'] == 'failure':
                run_jobs = self.get_connector_processor(github_actions_connector).get_jobs_list(owner, repo,
                                                                                                workflow_id)
                failures = []
                for run_job in run_jobs['jobs']:
                    if run_job['status'] == 'completed' and run_job['conclusion'] == 'failure':
                        job_id = run_job['id']
                        for step in run_job['steps']:
                            if step['status'] == 'completed' and step['conclusion'] == 'failure':
                                failures.append({"failed_step_name": step['name'], "failed_step_number": step['number'],
                                                 "run_attempt": run_job['run_attempt']})
                response_struct = dict_to_proto(
                    {"url": runs['html_url'], "workflow_id": workflow_id, "failures": failures}, Struct)
                failure_output = ApiResponseResult(response_body=response_struct)
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.API_RESPONSE,
                    source=self.source,
                    api_response=failure_output
                )
            else:
                response_struct = dict_to_proto(
                    {"url": runs['html_url'], "workflow_id": workflow_id, "failures": "No failures found in the run"},
                    Struct)
                return PlaybookTaskResult(
                    type=PlaybookTaskResultType.API_RESPONSE,
                    source=self.source,
                    api_response=ApiResponseResult(response_body=response_struct)
                )
        except Exception as e:
            raise Exception(f"Error while executing Github Actions fetch_action_run_info task: {e}")
