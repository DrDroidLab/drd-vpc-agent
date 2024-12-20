# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/assets/grafana_asset.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2
from protos import base_pb2 as protos_dot_base__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n!protos/assets/grafana_asset.proto\x12\x11protos.connectors\x1a\x1egoogle/protobuf/wrappers.proto\x1a\x11protos/base.proto\"\xf8\x08\n#GrafanaTargetMetricPromQlAssetModel\x12\x32\n\x0c\x64\x61shboard_id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x35\n\x0f\x64\x61shboard_title\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x33\n\rdashboard_url\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12_\n\x10panel_promql_map\x18\x04 \x03(\x0b\x32\x45.protos.connectors.GrafanaTargetMetricPromQlAssetModel.PanelPromqlMap\x1a\xfc\x04\n\x0cPromqlMetric\x12:\n\x14target_metric_ref_id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x34\n\x0e\x64\x61tasource_uid\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x30\n\nexpression\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12u\n\x12label_variable_map\x18\x04 \x03(\x0b\x32Y.protos.connectors.GrafanaTargetMetricPromQlAssetModel.PromqlMetric.QueryLabelVariableMap\x12~\n\x17variable_values_options\x18\x05 \x03(\x0b\x32].protos.connectors.GrafanaTargetMetricPromQlAssetModel.PromqlMetric.QueryVariableValueOptions\x1a[\n\x19QueryVariableValueOptions\x12.\n\x08variable\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x0e\n\x06values\x18\x02 \x03(\t\x1at\n\x15QueryLabelVariableMap\x12+\n\x05label\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12.\n\x08variable\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x1a\xd0\x01\n\x0ePanelPromqlMap\x12.\n\x08panel_id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x31\n\x0bpanel_title\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12[\n\x0epromql_metrics\x18\x03 \x03(\x0b\x32\x43.protos.connectors.GrafanaTargetMetricPromQlAssetModel.PromqlMetric\"\xc0\x05\n\x1bGrafanaDatasourceAssetModel\x12\x33\n\rdatasource_id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12\x34\n\x0e\x64\x61tasource_uid\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x34\n\x0e\x64\x61tasource_url\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x35\n\x0f\x64\x61tasource_name\x18\x05 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x35\n\x0f\x64\x61tasource_type\x18\x06 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x36\n\x10\x64\x61tasource_orgId\x18\x07 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12\x37\n\x11\x64\x61tasource_access\x18\x08 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x39\n\x13\x64\x61tasource_database\x18\t \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x37\n\x13\x64\x61tasource_readonly\x18\n \x01(\x0b\x32\x1a.google.protobuf.BoolValue\x12\x39\n\x13\x64\x61tasource_typeName\x18\x0b \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x38\n\x14\x64\x61tasource_basicAuth\x18\x0c \x01(\x0b\x32\x1a.google.protobuf.BoolValue\x12\x38\n\x14\x64\x61tasource_isDefault\x18\r \x01(\x0b\x32\x1a.google.protobuf.BoolValue\"\xc0\x04\n%GrafanaTargetMetricPromQlAssetOptions\x12\x64\n\ndashboards\x18\x01 \x03(\x0b\x32P.protos.connectors.GrafanaTargetMetricPromQlAssetOptions.GrafanaDashboardOptions\x1a\xb0\x03\n\x17GrafanaDashboardOptions\x12\x32\n\x0c\x64\x61shboard_id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x35\n\x0f\x64\x61shboard_title\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x33\n\rdashboard_url\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12{\n\rpanel_options\x18\x04 \x03(\x0b\x32\x64.protos.connectors.GrafanaTargetMetricPromQlAssetOptions.GrafanaDashboardOptions.GrafanaPanelOptions\x1ax\n\x13GrafanaPanelOptions\x12.\n\x08panel_id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x31\n\x0bpanel_title\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\"\xc9\x02\n\x1dGrafanaDatasourceAssetOptions\x12i\n\x16prometheus_datasources\x18\x01 \x03(\x0b\x32I.protos.connectors.GrafanaDatasourceAssetOptions.GrafanaDatasourceOptions\x1a\xbc\x01\n\x18GrafanaDatasourceOptions\x12\x33\n\rdatasource_id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12\x34\n\x0e\x64\x61tasource_uid\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x35\n\x0f\x64\x61tasource_name\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\"\xe4\x02\n\x11GrafanaAssetModel\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12&\n\x0e\x63onnector_type\x18\x02 \x01(\x0e\x32\x0e.protos.Source\x12%\n\x04type\x18\x03 \x01(\x0e\x32\x17.protos.SourceModelType\x12\x14\n\x0clast_updated\x18\x04 \x01(\x10\x12^\n\x1cgrafana_target_metric_promql\x18\x05 \x01(\x0b\x32\x36.protos.connectors.GrafanaTargetMetricPromQlAssetModelH\x00\x12W\n\x1dgrafana_prometheus_datasource\x18\x06 \x01(\x0b\x32..protos.connectors.GrafanaDatasourceAssetModelH\x00\x42\x07\n\x05\x61sset\"E\n\rGrafanaAssets\x12\x34\n\x06\x61ssets\x18\x01 \x03(\x0b\x32$.protos.connectors.GrafanaAssetModelb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.assets.grafana_asset_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _GRAFANATARGETMETRICPROMQLASSETMODEL._serialized_start=108
  _GRAFANATARGETMETRICPROMQLASSETMODEL._serialized_end=1252
  _GRAFANATARGETMETRICPROMQLASSETMODEL_PROMQLMETRIC._serialized_start=405
  _GRAFANATARGETMETRICPROMQLASSETMODEL_PROMQLMETRIC._serialized_end=1041
  _GRAFANATARGETMETRICPROMQLASSETMODEL_PROMQLMETRIC_QUERYVARIABLEVALUEOPTIONS._serialized_start=832
  _GRAFANATARGETMETRICPROMQLASSETMODEL_PROMQLMETRIC_QUERYVARIABLEVALUEOPTIONS._serialized_end=923
  _GRAFANATARGETMETRICPROMQLASSETMODEL_PROMQLMETRIC_QUERYLABELVARIABLEMAP._serialized_start=925
  _GRAFANATARGETMETRICPROMQLASSETMODEL_PROMQLMETRIC_QUERYLABELVARIABLEMAP._serialized_end=1041
  _GRAFANATARGETMETRICPROMQLASSETMODEL_PANELPROMQLMAP._serialized_start=1044
  _GRAFANATARGETMETRICPROMQLASSETMODEL_PANELPROMQLMAP._serialized_end=1252
  _GRAFANADATASOURCEASSETMODEL._serialized_start=1255
  _GRAFANADATASOURCEASSETMODEL._serialized_end=1959
  _GRAFANATARGETMETRICPROMQLASSETOPTIONS._serialized_start=1962
  _GRAFANATARGETMETRICPROMQLASSETOPTIONS._serialized_end=2538
  _GRAFANATARGETMETRICPROMQLASSETOPTIONS_GRAFANADASHBOARDOPTIONS._serialized_start=2106
  _GRAFANATARGETMETRICPROMQLASSETOPTIONS_GRAFANADASHBOARDOPTIONS._serialized_end=2538
  _GRAFANATARGETMETRICPROMQLASSETOPTIONS_GRAFANADASHBOARDOPTIONS_GRAFANAPANELOPTIONS._serialized_start=2418
  _GRAFANATARGETMETRICPROMQLASSETOPTIONS_GRAFANADASHBOARDOPTIONS_GRAFANAPANELOPTIONS._serialized_end=2538
  _GRAFANADATASOURCEASSETOPTIONS._serialized_start=2541
  _GRAFANADATASOURCEASSETOPTIONS._serialized_end=2870
  _GRAFANADATASOURCEASSETOPTIONS_GRAFANADATASOURCEOPTIONS._serialized_start=2682
  _GRAFANADATASOURCEASSETOPTIONS_GRAFANADATASOURCEOPTIONS._serialized_end=2870
  _GRAFANAASSETMODEL._serialized_start=2873
  _GRAFANAASSETMODEL._serialized_end=3229
  _GRAFANAASSETS._serialized_start=3231
  _GRAFANAASSETS._serialized_end=3300
# @@protoc_insertion_point(module_scope)
