from integrations.source_metadata_extractor import SourceMetadataExtractor
from integrations.source_api_processors.new_relic_graph_ql_processor import NewRelicGraphQlConnector
from protos.base_pb2 import Source, SourceModelType
from utils.logging_utils import log_function_call
from utils.static_mappings import NEWRELIC_APM_QUERIES

class NewrelicSourceMetadataExtractor(SourceMetadataExtractor):

    def __init__(self, request_id: str, connector_name: str, nr_api_key, nr_app_id, nr_api_domain='api.newrelic.com'):
        self.__gql_processor = NewRelicGraphQlConnector(nr_api_key, nr_app_id, nr_api_domain)

        super().__init__(request_id, connector_name, Source.NEW_RELIC)

    @log_function_call
    def extract_policy(self):
        model_type = SourceModelType.NEW_RELIC_POLICY
        cursor = 'null'
        policies = []
        policies_search = self.__gql_processor.get_all_policies(cursor)
        if 'policies' not in policies_search:
            return
        results = policies_search['policies']
        policies.extend(results)
        if 'nextCursor' in policies_search:
            cursor = policies_search['nextCursor']
        while cursor and cursor != 'null':
            policies_search = self.__gql_processor.get_all_policies(cursor)
            if 'policies' in policies_search:
                results = policies_search['policies']
                policies.extend(results)
                if 'nextCursor' in policies_search:
                    cursor = policies_search['nextCursor']
                else:
                    cursor = None
            else:
                break
        model_data = {}
        for policy in policies:
            policy_id = policy['id']
            model_data[policy_id] = policy
        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)

    def extract_entity(self):
        model_type = SourceModelType.NEW_RELIC_ENTITY
        cursor = 'null'
        types = ['HOST', 'MONITOR', 'WORKLOAD']
        entity_search = self.__gql_processor.get_all_entities(cursor, types)
        if 'results' not in entity_search:
            return
        results = entity_search['results']
        entities = []
        if 'entities' in results:
            entities.extend(results['entities'])
        if 'nextCursor' in results:
            cursor = results['nextCursor']
        while cursor and cursor != 'null':
            entity_search = self.__gql_processor.get_all_entities(cursor, types)
            if 'results' in entity_search:
                results = entity_search['results']
                if 'entities' in results:
                    entities.extend(results['entities'])
                if 'nextCursor' in results:
                    cursor = results['nextCursor']
                else:
                    cursor = None
            else:
                break
        model_data = {}
        for entity in entities:
            entity_guid = entity['guid']
            model_data[entity_guid] = entity
        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)

    def extract_condition(self):
        model_type = SourceModelType.NEW_RELIC_CONDITION
        cursor = 'null'
        conditions = []
        conditions_search = self.__gql_processor.get_all_conditions(cursor)
        if 'nrqlConditions' not in conditions_search:
            return
        results = conditions_search['nrqlConditions']
        conditions.extend(results)
        if 'nextCursor' in conditions_search:
            cursor = conditions_search['nextCursor']
        while cursor and cursor != 'null':
            conditions_search = self.__gql_processor.get_all_conditions(cursor)
            if 'nrqlConditions' in conditions_search:
                results = conditions_search['nrqlConditions']
                conditions.extend(results)
                if 'nextCursor' in conditions_search:
                    cursor = conditions_search['nextCursor']
                else:
                    cursor = None
            else:
                break
        model_data = {}
        for condition in conditions:
            condition_id = condition['id']
            model_data[condition_id] = condition
        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)

    def extract_dashboard_entity(self):
        model_type = SourceModelType.NEW_RELIC_ENTITY_DASHBOARD
        cursor = 'null'
        types = ['DASHBOARD']
        entity_search = self.__gql_processor.get_all_entities(cursor, types)
        if 'results' not in entity_search:
            return
        results = entity_search['results']
        entities = []
        if 'entities' in results:
            entities.extend(results['entities'])
        if 'nextCursor' in results:
            cursor = results['nextCursor']
        while cursor and cursor != 'null':
            entity_search = self.__gql_processor.get_all_entities(cursor, types)
            if 'results' in entity_search:
                results = entity_search['results']
                if 'entities' in results:
                    entities.extend(results['entities'])
                if 'nextCursor' in results:
                    cursor = results['nextCursor']
                else:
                    cursor = None
            else:
                break
        dashboard_entity_guid = [entity['guid'] for entity in entities]
        model_data = {}
        for i in range(0, len(dashboard_entity_guid), 25):
            dashboard_entity_search = self.__gql_processor.get_all_dashboard_entities(dashboard_entity_guid[i:i + 25])
            if not dashboard_entity_search or len(dashboard_entity_search) == 0:
                continue
            for entity in dashboard_entity_search:
                entity_id = entity['guid']
                model_data[entity_id] = entity
        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)

    def extract_application_entity(self):
        model_type = SourceModelType.NEW_RELIC_ENTITY_APPLICATION
        cursor = 'null'
        types = ['APPLICATION']
        entity_search = self.__gql_processor.get_all_entities(cursor, types)
        if 'results' not in entity_search:
            return
        results = entity_search['results']
        entities = []
        if 'entities' in results:
            entities.extend(results['entities'])
        if 'nextCursor' in results:
            cursor = results['nextCursor']
        while cursor and cursor != 'null':
            entity_search = self.__gql_processor.get_all_entities(cursor, types)
            if 'results' in entity_search:
                results = entity_search['results']
                if 'entities' in results:
                    entities.extend(results['entities'])
                if 'nextCursor' in results:
                    cursor = results['nextCursor']
                else:
                    cursor = None
            else:
                break
        model_data = {}
        for entity in entities:
            entity_guid = entity['guid']
            entity['apm_summary'] = []
            for metric_name, query in NEWRELIC_APM_QUERIES.items():
                formatted_query = query.replace('{}', f"'{entity_guid}'")
                apm_metric = {
                    'name': metric_name,
                    'unit': '',
                    'query': formatted_query
                }
                entity['apm_summary'].append(apm_metric)
            
            model_data[entity_guid] = entity
        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)

    def extract_dashboard_entity_v2(self):
        model_type = SourceModelType.NEW_RELIC_ENTITY_DASHBOARD_V2  
        cursor = 'null'
        types = ['DASHBOARD']
        entity_search = self.__gql_processor.get_all_entities(cursor, types)
        if 'results' not in entity_search:
            return
        results = entity_search['results']
        entities = []
        if 'entities' in results:
            entities.extend(results['entities'])
        if 'nextCursor' in results:
            cursor = results['nextCursor']
        while cursor and cursor != 'null':
            entity_search = self.__gql_processor.get_all_entities(cursor, types)
            if 'results' in entity_search:
                results = entity_search['results']
                if 'entities' in results:
                    entities.extend(results['entities'])
                if 'nextCursor' in results:
                    cursor = results['nextCursor']
                else:
                    cursor = None
            else:
                break
        dashboard_entity_guid = [entity['guid'] for entity in entities]
        model_data = {}
        for i in range(0, len(dashboard_entity_guid), 25):
            dashboard_entity_search = self.__gql_processor.get_all_dashboard_entities(dashboard_entity_guid[i:i + 25])
            if not dashboard_entity_search or len(dashboard_entity_search) == 0:
                continue
            for entity in dashboard_entity_search:
                entity_id = entity['guid']
                model_data[entity_id] = entity
        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)
