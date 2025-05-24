import logging
import json

from integrations.source_metadata_extractor import SourceMetadataExtractor
from integrations.source_api_processors.aws_boto_3_api_processor import AWSBoto3ApiProcessor
from protos.base_pb2 import Source, SourceModelType
from utils.logging_utils import log_function_call

logger = logging.getLogger(__name__)


def parse_query_string(query_string):
    parts = query_string.split('|', 1)
    return parts[1].strip() if len(parts) > 1 else query_string.strip()


ignored_db_names = ['information_schema', 'mysql', 'performance_schema', 'sys', 'Unknown']


class CloudwatchSourceMetadataExtractor(SourceMetadataExtractor):

    def __init__(self, request_id: str, connector_name: str, region, aws_access_key=None, aws_secret_key=None,
                 aws_assumed_role_arn=None, aws_drd_cloud_role_arn=None):
        self.__region = region
        self.__aws_access_key = aws_access_key
        self.__aws_secret_key = aws_secret_key
        self.__aws_assumed_role_arn = aws_assumed_role_arn
        self.__aws_drd_cloud_role_arn = aws_drd_cloud_role_arn

        super().__init__(request_id, connector_name, Source.CLOUDWATCH)

    @log_function_call
    def extract_metric(self):
        model_type = SourceModelType.CLOUDWATCH_METRIC
        model_data = {}
        try:
            cloudwatch_boto3_processor = AWSBoto3ApiProcessor('cloudwatch', self.__region, self.__aws_access_key,
                                                              self.__aws_secret_key, self.__aws_assumed_role_arn,
                                                              self.__aws_drd_cloud_role_arn)
            namespaces = ['AWS/AmplifyHosting',
                          'AWS/ApiGateway',
                          'AWS/AppFlow',
                          'AWS/MGN',
                          'AWS/AppRunner',
                          'AWS/AppStream',
                          'AWS/AppSync',
                          'AWS/Athena',
                          'AWS/RDS',
                          'AWS/Backup',
                          'AWS/Bedrock',
                          'AWS/Billing',
                          'AWS/Braket/By Device',
                          'AWS/CertificateManager',
                          'AWS/ACMPrivateCA',
                          'AWS/Chatbot',
                          'AWS/ChimeVoiceConnector',
                          'AWS/ChimeSDK',
                          'AWS/ClientVPN',
                          'AWS/CloudFront',
                          'AWS/CloudHSM',
                          'AWS/CloudSearch',
                          'AWS/CloudTrail',
                          'ApplicationSignals',
                          'AWS/CloudWatch/MetricStreams',
                          'AWS/RUM',
                          'CloudWatchSynthetics',
                          'AWS/Logs',
                          'AWS/CodeBuild',
                          'AWS/CodeWhisperer',
                          'AWS/Cognito',
                          'AWS/Comprehend',
                          'AWS/Config',
                          'AWS/Connect',
                          'AWS/DataLifecycleManager',
                          'AWS/DataSync',
                          'AWS/DevOps-Guru',
                          'AWS/DMS',
                          'AWS/DX',
                          'AWS/DirectoryService',
                          'AWS/DocDB',
                          'AWS/DynamoDB',
                          'AWS/DAX',
                          'AWS/EC2',
                          'AWS/ElasticGPUs',
                          'AWS/EC2Spot',
                          'AWS/AutoScaling',
                          'AWS/ElasticBeanstalk',
                          'AWS/EBS',
                          'AWS/ECR',
                          'AWS/ECS',
                          'ECS/ContainerInsights',
                          'AWS/ECS/ManagedScaling',
                          'AWS/EFS',
                          'AWS/ElasticInference',
                          'ContainerInsights',
                          'AWS/ApplicationELB',
                          'AWS/NetworkELB',
                          'AWS/GatewayELB',
                          'AWS/ELB',
                          'AWS/ElasticTranscoder',
                          'AWS/ElastiCache',
                          'AWS/ElastiCache',
                          'AWS/ES',
                          'AWS/ElasticMapReduce',
                          'AWS/MediaConnect',
                          'AWS/MediaConvert',
                          'AWS/MediaLive',
                          'AWS/MediaPackage',
                          'AWS/MediaStore',
                          'AWS/MediaTailor',
                          'AWS/SMSVoice',
                          'AWS/SocialMessaging',
                          'AWS/Events',
                          'AWS/FSx',
                          'AWS/FSx',
                          'AWS/FSx',
                          'AWS/FSx',
                          'AWS/FSx',
                          'AWS/GameLift',
                          'AWS/GlobalAccelerator',
                          'Glue',
                          'AWS/GroundStation',
                          'AWS/HealthLake',
                          'AWS/Inspector',
                          'AWS/IVS',
                          'AWS/IVSChat',
                          'AWS/IoT',
                          'AWS/IoTAnalytics',
                          'AWS/IoTFleetWise',
                          'AWS/IoTSiteWise',
                          'AWS/IoTTwinMaker',
                          'AWS/KMS',
                          'AWS/Cassandra',
                          'AWS/KinesisAnalytics',
                          'AWS/Firehose',
                          'AWS/Kinesis',
                          'AWS/KinesisVideo',
                          'AWS/Lambda',
                          'AWS/Lex',
                          'AWSLicenseManager/licenseUsage',
                          'AWS/LicenseManager/LinuxSubscriptions',
                          'AWS/Location',
                          'AWS/lookoutequipment',
                          'AWS/LookoutMetrics',
                          'AWS/LookoutVision',
                          'AWS/ML',
                          'AWS/managedblockchain',
                          'AWS/Prometheus',
                          'AWS/Kafka',
                          'AWS/KafkaConnect',
                          'AWS/MWAA',
                          'AWS/MemoryDB',
                          'AWS/AmazonMQ',
                          'AWS/Neptune',
                          'AWS/NetworkFirewall',
                          'AWS/NetworkManager',
                          'AWS/NimbleStudio',
                          'AWS/Omics',
                          'AWS/OpsWorks',
                          'AWS/Outposts',
                          'AWS/PanoramaDeviceMetrics',
                          'AWS/Personalize',
                          'AWS/Pinpoint',
                          'AWS/Polly',
                          'AWS/PrivateLinkEndpoints',
                          'AWS/PrivateLinkServices',
                          'AWS/Private5G',
                          'AWS/QLDB',
                          'AWS/QuickSight',
                          'AWS/Redshift',
                          'AWS/RDS',
                          'AWS/Rekognition',
                          'AWS/rePostPrivate',
                          'AWS/Robomaker',
                          'AWS/Route53',
                          'AWS/Route53RecoveryReadiness',
                          'AWS/SageMaker',
                          'AWS/SageMaker/ModelBuildingPipeline',
                          'AWS/SecretsManager',
                          'AWS/SecurityLake',
                          'AWS/ServiceCatalog',
                          'AWS/DDoSProtection',
                          'AWS/SES',
                          'AWS/simspaceweaver',
                          'AWS/SNS',
                          'AWS/SQS',
                          'AWS/S3',
                          'AWS/S3/Storage-Lens',
                          'AWS/SWF',
                          'AWS/States',
                          'AWS/StorageGateway',
                          'AWS/SSM-RunCommand',
                          'AWS/Textract',
                          'AWS/Timestream',
                          'AWS/Transfer',
                          'AWS/Transcribe',
                          'AWS/Translate',
                          'AWS/TrustedAdvisor',
                          'AWS/NATGateway',
                          'AWS/TransitGateway',
                          'AWS/VPN',
                          'AWS/IPAM',
                          'AWS/WAFV2',
                          'WAF',
                          'AWS/WorkMail',
                          'AWS/WorkSpaces',
                          'AWS/WorkSpacesWeb']
            for namespace in namespaces:
                iterator = 0
                next_token = None
                metric_dimension_map = {}
                while True:
                    response = cloudwatch_boto3_processor.cloudwatch_list_metrics(namespace, next_token)
                    next_token = response.get('NextToken', None)
                    all_metrics = response.get('Metrics', [])
                    iterator += 1
                    for metric in all_metrics:
                        metric_map = metric_dimension_map.get(metric['MetricName'], {})
                        dimension_map = metric_map.get('Dimensions', {})
                        for dimension in metric['Dimensions']:
                            dimension_values = dimension_map.get(dimension['Name'], [])
                            dimension_values.append(dimension['Value'])
                            dimension_map[dimension['Name']] = list(set(dimension_values))
                        metric_dimension_map[metric['MetricName']] = {'Dimensions': dimension_map,
                                                                      'DimensionNames': list(dimension_map.keys())}
                    if not next_token or next_token == '':
                        break

                model_data[namespace] = {self.__region: metric_dimension_map}

            if len(model_data) > 0:
                self.create_or_update_model_metadata(model_type, model_data)
        except Exception as e:
            raise e

    @log_function_call
    def extract_log_groups(self):
        model_type = SourceModelType.CLOUDWATCH_LOG_GROUP
        model_data = {}
        cloudwatch_boto3_processor = AWSBoto3ApiProcessor('logs', self.__region, self.__aws_access_key,
                                                          self.__aws_secret_key, self.__aws_assumed_role_arn,
                                                          self.__aws_drd_cloud_role_arn)
        try:
            all_log_groups = cloudwatch_boto3_processor.logs_describe_log_groups()
            model_data[self.__region] = {'log_groups': all_log_groups}
        except Exception as e:
            logger.error(f'Error extracting cloudwatch log groups: {e}')
        
        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)

    @log_function_call
    def extract_log_group_queries(self):
        model_type = SourceModelType.CLOUDWATCH_LOG_GROUP_QUERY
        model_data = {}
        cloudwatch_boto3_processor = AWSBoto3ApiProcessor('logs', self.__region, self.__aws_access_key,
                                                          self.__aws_secret_key, self.__aws_assumed_role_arn,
                                                          self.__aws_drd_cloud_role_arn)
        try:
            all_queries = cloudwatch_boto3_processor.logs_describe_log_group_queries()

            parsed_queries_by_group = {}
            for query in all_queries:
                log_group_name = query['logGroupName']
                parsed_query = parse_query_string(query['queryString'])

                if log_group_name not in parsed_queries_by_group:
                    parsed_queries_by_group[log_group_name] = set()

                parsed_queries_by_group[log_group_name].add(parsed_query)

            # Convert sets to lists
            parsed_queries_by_group = {group: list(queries) for group, queries in parsed_queries_by_group.items()}

            for log_group, queries in parsed_queries_by_group.items():
                model_data[log_group] = {'queries': queries}
        except Exception as e:
            logger.error(f'Error extracting cloudwatch log group queries: {e}')

        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)

    @log_function_call
    def extract_alarms(self):
        model_type = SourceModelType.CLOUDWATCH_ALARMS
        model_data = {}
        cloudwatch_boto3_processor = AWSBoto3ApiProcessor('cloudwatch', self.__region, self.__aws_access_key,
                                                          self.__aws_secret_key, self.__aws_assumed_role_arn,
                                                          self.__aws_drd_cloud_role_arn)
        try:
            all_alarms = cloudwatch_boto3_processor.cloudwatch_describe_all_alarms()

            for alarm in all_alarms.get('MetricAlarms', []) + all_alarms.get('CompositeAlarms', []):
                alarm_name = alarm['AlarmName']
                model_data[alarm_name] = alarm

        except Exception as e:
            logger.error(f'Error extracting CloudWatch alarms: {e}')
        
        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)

    @log_function_call
    def extract_ecs_clusters(self):
        model_type = SourceModelType.ECS_CLUSTER
        model_data = {}
        
        # Create ECS boto3 processor
        ecs_boto3_processor = AWSBoto3ApiProcessor('ecs', self.__region, self.__aws_access_key,
                                                  self.__aws_secret_key, self.__aws_assumed_role_arn,
                                                  self.__aws_drd_cloud_role_arn)
        try:
            # Get all clusters
            clusters = ecs_boto3_processor.list_all_clusters()
            
            if not clusters:
                return model_data
                
            # Process each cluster
            for cluster in clusters:
                cluster_name = cluster.get('clusterName')
                cluster_arn = cluster.get('clusterArn')
                
                # Get services for this cluster
                services = ecs_boto3_processor.list_services_in_cluster(cluster_arn)
                service_names = [service.get('serviceName') for service in services] if services else []
                
                # Get tasks for this cluster
                tasks = ecs_boto3_processor.list_tasks_in_cluster(cluster_arn)
                
                # Extract container names from tasks
                container_names = []
                if tasks:
                    for task in tasks:
                        for container in task.get('containers', []):
                            container_name = container.get('name')
                            if container_name and container_name not in container_names:
                                container_names.append(container_name)
                
                # Create metadata for this cluster
                cluster_metadata = {
                    'cluster_name': cluster_name,
                    'services': service_names,
                    'containers': container_names,
                    'region': self.__region  # Include region for reference
                }
                
                # Store metadata with cluster name as model_uid
                model_data[cluster_name] = cluster_metadata
                    
        except Exception as e:
            logger.error(f'Error extracting ECS clusters: {e}')
            
        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)
        
    @log_function_call
    def extract_ecs_tasks(self):
        model_type = SourceModelType.ECS_TASK
        model_data = {}
        
        # Create ECS boto3 processor
        ecs_boto3_processor = AWSBoto3ApiProcessor('ecs', self.__region, self.__aws_access_key,
                                                  self.__aws_secret_key, self.__aws_assumed_role_arn,
                                                  self.__aws_drd_cloud_role_arn)
        try:
            # Get all clusters first
            clusters = ecs_boto3_processor.list_all_clusters()
            
            if not clusters:
                return model_data
                
            # Process each cluster to get its tasks
            for cluster in clusters:
                cluster_name = cluster.get('clusterName')
                cluster_arn = cluster.get('clusterArn')
                
                # Get tasks for this cluster
                tasks = ecs_boto3_processor.list_tasks_in_cluster(cluster_arn)
                
                if not tasks:
                    continue
                    
                # Process each task
                for task in tasks:
                    task_arn = task.get('taskArn')
                    task_id = task_arn.split('/')[-1]  # Extract task ID from ARN
                    task_definition_arn = task.get('taskDefinitionArn')
                    status = task.get('lastStatus')
                    
                    # Get container information
                    container_name = ""
                    if task.get('containers') and len(task.get('containers')) > 0:
                        container_name = task.get('containers')[0].get('name', "")
                    
                    # Create metadata for this task
                    task_metadata = {
                        'taskArn': task_arn,
                        'clusterName': cluster_name,
                        'clusterArn': cluster_arn,
                        'taskDefinitionArn': task_definition_arn,
                        'status': status,
                        'container_name': container_name,
                        'region': self.__region
                    }
                    
                    # Store metadata with task ARN as model_uid
                    model_data[task_arn] = task_metadata
                    
                        
        except Exception as e:
            logger.error(f'Error extracting ECS tasks: {e}')
            
        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)
        
    @log_function_call
    def extract_rds_instances(self):
        model_type = SourceModelType.RDS_INSTANCES
        model_data = {}
        try:
            rds_boto3_processor = AWSBoto3ApiProcessor('rds', self.__region, self.__aws_access_key,
                                                       self.__aws_secret_key, self.__aws_assumed_role_arn,
                                                       self.__aws_drd_cloud_role_arn)
            pi_boto3_processor = AWSBoto3ApiProcessor('pi', self.__region, self.__aws_access_key,
                                                      self.__aws_secret_key, self.__aws_assumed_role_arn,
                                                      self.__aws_drd_cloud_role_arn)
        except Exception as e:
            logger.error(f'Error creating boto3 processors: {e}')
            return {}
        try:
            rds_instances = rds_boto3_processor.rds_describe_instances()
            if rds_instances and 'DBInstances' in rds_instances:
                for db_detail in rds_instances['DBInstances']:
                    model_data[db_detail['DBInstanceIdentifier']] = db_detail
                    try:
                        db_resource_uri = db_detail['DbiResourceId']
                        db_detail['db_names'] = []
                        all_db_names = pi_boto3_processor.pi_describe_db_dimension_keys(db_resource_uri)
                        if all_db_names:
                            db_detail['db_names'] = [db_name for db_name in all_db_names if
                                                     db_name not in ignored_db_names]
                            db_detail['db_names'] = list(set(db_detail['db_names']))
                    except Exception as e:
                        logger.error(
                            f'Error fetching Performance Insights data for RDS instance {db_detail["DBInstanceIdentifier"]}: {e}')
                        db_detail['db_names'] = []
        except Exception as e:
            logger.error(f'Error extracting RDS instances: {e}')
        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)

    @log_function_call
    def extract_dashboards(self):
        model_type = SourceModelType.CLOUDWATCH_DASHBOARD
        model_data = {}
        cloudwatch_boto3_processor = AWSBoto3ApiProcessor('cloudwatch', self.__region, self.__aws_access_key,
                                                          self.__aws_secret_key, self.__aws_assumed_role_arn,
                                                          self.__aws_drd_cloud_role_arn)
        # Get client directly for get_dashboard call later
        client = cloudwatch_boto3_processor.get_connection()

        try:
            # Use the new processor method to list dashboards
            dashboard_entries = cloudwatch_boto3_processor.cloudwatch_list_dashboards()

            for dashboard_entry in dashboard_entries:
                dashboard_name = dashboard_entry.get('DashboardName')
                dashboard_arn = dashboard_entry.get('DashboardArn')
                if not dashboard_name:
                    continue

                try:
                    # Use processor method to get dashboard details
                    dashboard_detail = cloudwatch_boto3_processor.cloudwatch_get_dashboard(dashboard_name)
                    if not dashboard_detail:
                        logger.warning(f"Could not fetch details for dashboard '{dashboard_name}', skipping.")
                        continue

                    dashboard_body_str = dashboard_detail.get('DashboardBody')
                    if not dashboard_body_str:
                        continue

                    dashboard_body = json.loads(dashboard_body_str)
                    widgets_data = []
                    for widget in dashboard_body.get('widgets', []):
                        widget_type = widget.get('type', 'metric')
                        properties = widget.get('properties', {})
                        region = properties.get('region', self.__region)
                        title = properties.get('title', '')

                        if widget_type == 'metric':
                            metrics = properties.get('metrics', [])
                            period = properties.get('period', 300)
                            stat = properties.get('stat', 'Average')

                            # Metrics can be defined in a nested list structure for 'metric' type
                            flat_metrics = []
                            if isinstance(metrics, list):
                                for item in metrics:
                                    # If item is a list, it represents a single metric definition
                                    if isinstance(item, list):
                                        flat_metrics.append(item)
                                    # It might be a list containing lists (older format?)
                                    elif isinstance(item, list) and all(isinstance(sub_item, list) for sub_item in item):
                                         flat_metrics.extend(item)
                                    # Skip other unexpected structures
                                    else:
                                        logger.warning(f"Skipping unexpected item format in 'metric' widget metrics list: {item}")


                            for metric_details_list in flat_metrics:
                                # Expecting list like: [ Namespace, MetricName, [DimName1, DimValue1], ..., { options } ]
                                # Or simpler: [ Namespace, MetricName, DimName1, DimValue1, ... ]

                                if not isinstance(metric_details_list, list) or len(metric_details_list) < 2:
                                    logger.warning(f"Skipping invalid metric format in 'metric' widget: {metric_details_list}")
                                    continue

                                namespace = metric_details_list[0]
                                metric_name = metric_details_list[1]
                                dimensions = []
                                widget_stat = stat # Use widget-level stat unless overridden in options
                                widget_period = int(period)
                                unit = None # Default unit

                                # Check for options dict at the end
                                metric_options = {}
                                if len(metric_details_list) > 2 and isinstance(metric_details_list[-1], dict):
                                    metric_options = metric_details_list.pop() # Remove options dict
                                    widget_stat = metric_options.get('stat', stat)
                                    widget_period = metric_options.get('period', period)
                                    unit = metric_options.get('unit', None)
                                    region = metric_options.get('region', region)

                                # Process remaining items as dimensions (assuming pairs or Name/Value dicts)
                                dim_items = metric_details_list[2:]
                                i = 0
                                while i < len(dim_items):
                                    # Check for {Name: ..., Value: ...} dict - less common?
                                    if isinstance(dim_items[i], dict) and 'Name' in dim_items[i] and 'Value' in dim_items[i]:
                                        dimensions.append({'Name': dim_items[i]['Name'], 'Value': dim_items[i]['Value']})
                                        i += 1
                                    # Assume Name, Value pairs
                                    elif i + 1 < len(dim_items):
                                        dimensions.append({'Name': str(dim_items[i]), 'Value': str(dim_items[i+1])})
                                        i += 2
                                    else:
                                        logger.warning(f"Skipping dimension pair in 'metric' widget due to uneven items: {dim_items[i:]}")
                                        break # Stop processing dimensions for this metric

                                if namespace and metric_name:
                                    widgets_data.append({
                                        'namespace': namespace,
                                        'metric_name': metric_name,
                                        'dimensions': dimensions,
                                        'statistic': widget_stat,
                                        'period': int(widget_period),
                                        'region': region,
                                        'unit': unit,
                                        'widget_title': title
                                    })
                                else:
                                     logger.warning(f"Missing namespace or metric name in parsed metric widget details: {metric_details_list}")


                        elif widget_type == 'explorer':
                            logger.warning(f"Skipping widget type 'explorer' in dashboard '{dashboard_name}' as it's not directly mappable to specific metrics.")
                            continue # Skip explorer widgets for now

                        elif widget_type in ['log', 'alarm', 'text']:
                             logger.info(f"Skipping widget type '{widget_type}' in dashboard '{dashboard_name}'.")
                             continue # Skip log, alarm, text for now, primary focus is metrics.

                        else:
                            logger.warning(f"Skipping unknown widget type '{widget_type}' in dashboard '{dashboard_name}'.")
                            continue

                    if widgets_data:
                        dashboard_metadata = {
                            'dashboard_name': dashboard_name,
                            'dashboard_arn': dashboard_arn,
                            'widgets': widgets_data,
                            'region': self.__region # Store the primary region this was extracted from
                        }
                        model_data[dashboard_name] = dashboard_metadata

                except Exception as e:
                    logger.error(f'Error processing dashboard {dashboard_name}: {e}')
                    continue # Skip this dashboard if parsing fails

        except Exception as e:
            logger.error(f'Error listing or fetching CloudWatch dashboards: {e}')

        if len(model_data) > 0:
            self.create_or_update_model_metadata(model_type, model_data)

