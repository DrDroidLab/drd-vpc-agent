import logging

from google.protobuf.wrappers_pb2 import StringValue

from integrations.source_api_processors.smtp_api_processor import SmtpApiProcessor
from integrations.source_manager import SourceManager
from protos.base_pb2 import Source, TimeRange
from protos.connectors.connector_pb2 import Connector as ConnectorProto
from protos.literal_pb2 import LiteralType
from protos.playbooks.playbook_commons_pb2 import PlaybookTaskResult, PlaybookTaskResultType

from protos.playbooks.source_task_definitions.email_task_pb2 import SMTP
from protos.ui_definition_pb2 import FormField, FormFieldType
from utils.credentilal_utils import generate_credentials_dict

logger = logging.getLogger(__name__)


class SMTPSourceManager(SourceManager):

    def __init__(self):
        self.source = Source.SMTP
        self.task_proto = SMTP
        self.task_type_callable_map = {
            SMTP.TaskType.SEND_EMAIL: {
                'executor': self.execute_send_email,
                'model_types': [],
                'result_type': PlaybookTaskResultType.UNKNOWN,
                'display_name': 'Send an email using SMTP',
                'category': 'Actions',
                'form_fields': [
                    FormField(key_name=StringValue(value="to"),
                              display_name=StringValue(value="To"),
                              description=StringValue(value='Enter To'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="subject"),
                              display_name=StringValue(value="Subject"),
                              description=StringValue(value='Enter Subject'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.TEXT_FT),
                    FormField(key_name=StringValue(value="body"),
                              display_name=StringValue(value="Body"),
                              description=StringValue(value='Enter Body'),
                              data_type=LiteralType.STRING,
                              form_field_type=FormFieldType.MULTILINE_FT),
                ]
            },
        }

    def get_connector_processor(self, smtp_connector, **kwargs):
        generated_credentials = generate_credentials_dict(smtp_connector.type, smtp_connector.keys)
        return SmtpApiProcessor(**generated_credentials)

    def execute_send_email(self, time_range: TimeRange, smtp_task: SMTP,
                           smtp_connector: ConnectorProto):
        try:
            if not smtp_connector:
                raise Exception("Task execution Failed:: No SMTP source found")

            send_email_task: SMTP.SendEmail = smtp_task.send_email
            to_email = send_email_task.to.value
            subject = send_email_task.subject.value
            body = send_email_task.body.value

            if not to_email or not subject or not body:
                raise Exception("Task execution Failed:: Missing required email fields")

            smtp_api_processor = self.get_connector_processor(smtp_connector)
            print(f"Playbook Task Downstream Request: Type -> SMTP, To -> {to_email}", flush=True)

            smtp_api_processor.send_email(to_email, subject, body)

            return PlaybookTaskResult(source=self.source)
        except Exception as e:
            raise Exception(f"Error while executing SMTP task: {e}")
