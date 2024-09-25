import logging

from asset_manager.extractor.metadata_extractor import SourceMetadataExtractor
from integrations.source_processors.pd_api_processor import PdApiProcessor
from protos.base_pb2 import Source, SourceModelType
from datetime import datetime, timedelta

from utils.logging_utils import log_function_call

logger = logging.getLogger(__name__)


class PagerDutyConnectorMetadataExtractor(SourceMetadataExtractor):

    def __init__(self, api_key, configured_email, account_id=None, connector_id=None):
        self.__client = PdApiProcessor(api_key, configured_email)
        super().__init__(account_id, connector_id, Source.PAGER_DUTY)

    @log_function_call
    def extract_alerts(self, save_to_db=False):
        model_type = SourceModelType.PAGERDUTY_INCIDENT
        try:
            since_time = (datetime.utcnow() - timedelta(days=7)).isoformat() + 'Z'
            incidents = self.__client.fetch_incidents()
            if not incidents:
                logger.info('No incidents found')
                return
            recent_alerts = {}
            for incident in incidents:
                incident_id = incident.get('id', '')
                if not incident_id:
                    continue
                alerts = self.__client.fetch_alerts(incident_id)
                filtered_alerts = [alert for alert in alerts if alert.get('created_at') >= since_time]
                if filtered_alerts:
                    recent_alerts[incident_id] = filtered_alerts
        except Exception as e:
            logger.error(f'Error fetching incidents: {e}')
            return
        if not recent_alerts:
            return
        model_data = {}
        for incident_id, alerts in recent_alerts.items():
            try:
                detailed_alerts = []
                for alert in alerts:
                    alert_id = alert.get('id', '')
                    details = alert.get('body', {}).get('details', {})
                    detailed_alert = {
                        'alert': alert,
                        'details': details
                    }
                    detailed_alerts.append(detailed_alert)
                model_data[incident_id] = detailed_alerts
                if save_to_db:
                    self.create_or_update_model_metadata(model_type, incident_id, detailed_alerts)
            except Exception as e:
                logger.error(f'Error processing alerts for incident {incident_id}: {e}')
                continue
        return model_data
