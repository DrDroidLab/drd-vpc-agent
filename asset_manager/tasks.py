import logging

from celery import shared_task

from drdroid_debug_toolkit.core.integrations.source_metadata_extractor import SourceMetadataExtractor
from drdroid_debug_toolkit.core.integrations.source_metadata_extractor_facade import source_metadata_extractor_facade

logger = logging.getLogger(__name__)


@shared_task(max_retries=3, default_retry_delay=10)
def populate_connector_metadata(request_id, connector_name, connector_type, connector_credentials_dict):
    logger.info(f"Running populate_connector_metadata for connector: {connector_name} with request_id: {request_id}")
    try:
        extractor_class = source_metadata_extractor_facade.get_connector_metadata_extractor_class(connector_type)
    except Exception as e:
        logger.warning(f"Exception occurred while fetching extractor class for connector: {connector_name}, "
                       f"with error: {e}")
        return False
    extractor = extractor_class(request_id=request_id, connector_name=connector_name, **connector_credentials_dict)
    extractor_methods = [method for method in dir(extractor) if
                         callable(getattr(extractor, method)) and method not in dir(SourceMetadataExtractor)]
    for extractor_method in extractor_methods:
        logger.info(f"Running method: {extractor_method} for connector: {connector_name}")
        try:
            extractor_async_method_call.delay(request_id, connector_name, connector_type, connector_credentials_dict,
                                              extractor_method)
        except Exception as e:
            logger.error(
                f"Exception occurred while scheduling method: {extractor_method} for connector: {connector_name}, "
                f"with error: {e}")
            continue


@shared_task(max_retries=3, default_retry_delay=10)
def extractor_async_method_call(request_id, connector_name, connector_type, connector_credentials_dict,
                                extractor_method):
    logger.info(f"Running extractor_async_method_call: {extractor_method} for connector: {connector_name} with "
                f"request_id: {request_id}")
    extractor_class = source_metadata_extractor_facade.get_connector_metadata_extractor_class(connector_type)
    extractor = extractor_class(request_id=request_id, connector_name=connector_name, **connector_credentials_dict)
    method = getattr(extractor, extractor_method)
    try:
        method()
    except Exception as e:
        logger.error(f"Exception occurred while running method: {extractor_method} for connector: {connector_name}, "
                     f"request ID: {request_id}, with error: {e}")
        return False
    return True
