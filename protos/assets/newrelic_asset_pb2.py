# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/assets/newrelic_asset.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2
from protos import base_pb2 as protos_dot_base__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\"protos/assets/newrelic_asset.proto\x12\x11protos.connectors\x1a\x1egoogle/protobuf/wrappers.proto\x1a\x11protos/base.proto\"\xc3\x03\n#NewRelicApplicationEntityAssetModel\x12=\n\x17\x61pplication_entity_guid\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x36\n\x10\x61pplication_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12[\n\x0egolden_metrics\x18\x03 \x03(\x0b\x32\x43.protos.connectors.NewRelicApplicationEntityAssetModel.GoldenMetric\x1a\xc7\x01\n\x0cGoldenMetric\x12\x38\n\x12golden_metric_name\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x38\n\x12golden_metric_unit\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x43\n\x1dgolden_metric_nrql_expression\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\"B\n%NewRelicApplicationEntityAssetOptions\x12\x19\n\x11\x61pplication_names\x18\x01 \x03(\t\"\x8d\x05\n!NewRelicDashboardEntityAssetModel\x12\x34\n\x0e\x64\x61shboard_guid\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x34\n\x0e\x64\x61shboard_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12Q\n\x05pages\x18\x03 \x03(\x0b\x32\x42.protos.connectors.NewRelicDashboardEntityAssetModel.DashboardPage\x1a\xe2\x01\n\nPageWidget\x12/\n\twidget_id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x32\n\x0cwidget_title\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x31\n\x0bwidget_type\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12<\n\x16widget_nrql_expression\x18\x04 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x1a\xc3\x01\n\rDashboardPage\x12/\n\tpage_guid\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12/\n\tpage_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12P\n\x07widgets\x18\x03 \x03(\x0b\x32?.protos.connectors.NewRelicDashboardEntityAssetModel.PageWidget\"\xf1\x03\n#NewRelicDashboardEntityAssetOptions\x12[\n\ndashboards\x18\x01 \x03(\x0b\x32G.protos.connectors.NewRelicDashboardEntityAssetOptions.DashboardOptions\x1a\xec\x02\n\x10\x44\x61shboardOptions\x12\x34\n\x0e\x64\x61shboard_guid\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x34\n\x0e\x64\x61shboard_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12r\n\x0cpage_options\x18\x04 \x03(\x0b\x32\\.protos.connectors.NewRelicDashboardEntityAssetOptions.DashboardOptions.DashboardPageOptions\x1ax\n\x14\x44\x61shboardPageOptions\x12/\n\tpage_guid\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12/\n\tpage_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\"\xe8\x02\n\x12NewRelicAssetModel\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12&\n\x0e\x63onnector_type\x18\x02 \x01(\x0e\x32\x0e.protos.Source\x12%\n\x04type\x18\x03 \x01(\x0e\x32\x17.protos.SourceModelType\x12\x14\n\x0clast_updated\x18\x04 \x01(\x10\x12^\n\x1cnew_relic_entity_application\x18\x05 \x01(\x0b\x32\x36.protos.connectors.NewRelicApplicationEntityAssetModelH\x00\x12Z\n\x1anew_relic_entity_dashboard\x18\x06 \x01(\x0b\x32\x34.protos.connectors.NewRelicDashboardEntityAssetModelH\x00\x42\x07\n\x05\x61sset\"G\n\x0eNewRelicAssets\x12\x35\n\x06\x61ssets\x18\x01 \x03(\x0b\x32%.protos.connectors.NewRelicAssetModelb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.assets.newrelic_asset_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _NEWRELICAPPLICATIONENTITYASSETMODEL._serialized_start=109
  _NEWRELICAPPLICATIONENTITYASSETMODEL._serialized_end=560
  _NEWRELICAPPLICATIONENTITYASSETMODEL_GOLDENMETRIC._serialized_start=361
  _NEWRELICAPPLICATIONENTITYASSETMODEL_GOLDENMETRIC._serialized_end=560
  _NEWRELICAPPLICATIONENTITYASSETOPTIONS._serialized_start=562
  _NEWRELICAPPLICATIONENTITYASSETOPTIONS._serialized_end=628
  _NEWRELICDASHBOARDENTITYASSETMODEL._serialized_start=631
  _NEWRELICDASHBOARDENTITYASSETMODEL._serialized_end=1284
  _NEWRELICDASHBOARDENTITYASSETMODEL_PAGEWIDGET._serialized_start=860
  _NEWRELICDASHBOARDENTITYASSETMODEL_PAGEWIDGET._serialized_end=1086
  _NEWRELICDASHBOARDENTITYASSETMODEL_DASHBOARDPAGE._serialized_start=1089
  _NEWRELICDASHBOARDENTITYASSETMODEL_DASHBOARDPAGE._serialized_end=1284
  _NEWRELICDASHBOARDENTITYASSETOPTIONS._serialized_start=1287
  _NEWRELICDASHBOARDENTITYASSETOPTIONS._serialized_end=1784
  _NEWRELICDASHBOARDENTITYASSETOPTIONS_DASHBOARDOPTIONS._serialized_start=1420
  _NEWRELICDASHBOARDENTITYASSETOPTIONS_DASHBOARDOPTIONS._serialized_end=1784
  _NEWRELICDASHBOARDENTITYASSETOPTIONS_DASHBOARDOPTIONS_DASHBOARDPAGEOPTIONS._serialized_start=1664
  _NEWRELICDASHBOARDENTITYASSETOPTIONS_DASHBOARDOPTIONS_DASHBOARDPAGEOPTIONS._serialized_end=1784
  _NEWRELICASSETMODEL._serialized_start=1787
  _NEWRELICASSETMODEL._serialized_end=2147
  _NEWRELICASSETS._serialized_start=2149
  _NEWRELICASSETS._serialized_end=2220
# @@protoc_insertion_point(module_scope)
