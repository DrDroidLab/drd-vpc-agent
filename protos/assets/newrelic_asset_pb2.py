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


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\"protos/assets/newrelic_asset.proto\x12\x11protos.connectors\x1a\x1egoogle/protobuf/wrappers.proto\x1a\x11protos/base.proto\"\xd2\x05\n#NewRelicApplicationEntityAssetModel\x12=\n\x17\x61pplication_entity_guid\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x36\n\x10\x61pplication_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12[\n\x0egolden_metrics\x18\x03 \x03(\x0b\x32\x43.protos.connectors.NewRelicApplicationEntityAssetModel.GoldenMetric\x12X\n\x0b\x61pm_metrics\x18\x04 \x03(\x0b\x32\x43.protos.connectors.NewRelicApplicationEntityAssetModel.APMDashboard\x1a\xc7\x01\n\x0cGoldenMetric\x12\x38\n\x12golden_metric_name\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x38\n\x12golden_metric_unit\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x43\n\x1dgolden_metric_nrql_expression\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x1a\xb2\x01\n\x0c\x41PMDashboard\x12\x31\n\x0bmetric_name\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x31\n\x0bmetric_unit\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12<\n\x16metric_nrql_expression\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\"B\n%NewRelicApplicationEntityAssetOptions\x12\x19\n\x11\x61pplication_names\x18\x01 \x03(\t\"\x8d\x05\n!NewRelicDashboardEntityAssetModel\x12\x34\n\x0e\x64\x61shboard_guid\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x34\n\x0e\x64\x61shboard_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12Q\n\x05pages\x18\x03 \x03(\x0b\x32\x42.protos.connectors.NewRelicDashboardEntityAssetModel.DashboardPage\x1a\xe2\x01\n\nPageWidget\x12/\n\twidget_id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x32\n\x0cwidget_title\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x31\n\x0bwidget_type\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12<\n\x16widget_nrql_expression\x18\x04 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x1a\xc3\x01\n\rDashboardPage\x12/\n\tpage_guid\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12/\n\tpage_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12P\n\x07widgets\x18\x03 \x03(\x0b\x32?.protos.connectors.NewRelicDashboardEntityAssetModel.PageWidget\"\xf1\x03\n#NewRelicDashboardEntityAssetOptions\x12[\n\ndashboards\x18\x01 \x03(\x0b\x32G.protos.connectors.NewRelicDashboardEntityAssetOptions.DashboardOptions\x1a\xec\x02\n\x10\x44\x61shboardOptions\x12\x34\n\x0e\x64\x61shboard_guid\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x34\n\x0e\x64\x61shboard_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12r\n\x0cpage_options\x18\x04 \x03(\x0b\x32\\.protos.connectors.NewRelicDashboardEntityAssetOptions.DashboardOptions.DashboardPageOptions\x1ax\n\x14\x44\x61shboardPageOptions\x12/\n\tpage_guid\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12/\n\tpage_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\"\x9c\x05\n#NewRelicDashboardEntityAssetModelV2\x12\x34\n\x0e\x64\x61shboard_guid\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x34\n\x0e\x64\x61shboard_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12U\n\x05pages\x18\x03 \x03(\x0b\x32\x46.protos.connectors.NewRelicDashboardEntityAssetModelV2.DashboardPageV2\x1a\xe5\x01\n\x0cPageWidgetV2\x12/\n\twidget_id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x32\n\x0cwidget_title\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x31\n\x0bwidget_type\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12=\n\x17widget_nrql_expressions\x18\x04 \x03(\x0b\x32\x1c.google.protobuf.StringValue\x1a\xc9\x01\n\x0f\x44\x61shboardPageV2\x12/\n\tpage_guid\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12/\n\tpage_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12T\n\x07widgets\x18\x03 \x03(\x0b\x32\x43.protos.connectors.NewRelicDashboardEntityAssetModelV2.PageWidgetV2\"\x81\x04\n%NewRelicDashboardEntityAssetOptionsV2\x12_\n\ndashboards\x18\x01 \x03(\x0b\x32K.protos.connectors.NewRelicDashboardEntityAssetOptionsV2.DashboardOptionsV2\x1a\xf6\x02\n\x12\x44\x61shboardOptionsV2\x12\x34\n\x0e\x64\x61shboard_guid\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x34\n\x0e\x64\x61shboard_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12x\n\x0cpage_options\x18\x04 \x03(\x0b\x32\x62.protos.connectors.NewRelicDashboardEntityAssetOptionsV2.DashboardOptionsV2.DashboardPageOptionsV2\x1az\n\x16\x44\x61shboardPageOptionsV2\x12/\n\tpage_guid\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12/\n\tpage_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\"\xc9\x03\n\x12NewRelicAssetModel\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12&\n\x0e\x63onnector_type\x18\x02 \x01(\x0e\x32\x0e.protos.Source\x12%\n\x04type\x18\x03 \x01(\x0e\x32\x17.protos.SourceModelType\x12\x14\n\x0clast_updated\x18\x04 \x01(\x10\x12^\n\x1cnew_relic_entity_application\x18\x05 \x01(\x0b\x32\x36.protos.connectors.NewRelicApplicationEntityAssetModelH\x00\x12Z\n\x1anew_relic_entity_dashboard\x18\x06 \x01(\x0b\x32\x34.protos.connectors.NewRelicDashboardEntityAssetModelH\x00\x12_\n\x1dnew_relic_entity_dashboard_v2\x18\x07 \x01(\x0b\x32\x36.protos.connectors.NewRelicDashboardEntityAssetModelV2H\x00\x42\x07\n\x05\x61sset\"G\n\x0eNewRelicAssets\x12\x35\n\x06\x61ssets\x18\x01 \x03(\x0b\x32%.protos.connectors.NewRelicAssetModelb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.assets.newrelic_asset_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _NEWRELICAPPLICATIONENTITYASSETMODEL._serialized_start=109
  _NEWRELICAPPLICATIONENTITYASSETMODEL._serialized_end=831
  _NEWRELICAPPLICATIONENTITYASSETMODEL_GOLDENMETRIC._serialized_start=451
  _NEWRELICAPPLICATIONENTITYASSETMODEL_GOLDENMETRIC._serialized_end=650
  _NEWRELICAPPLICATIONENTITYASSETMODEL_APMDASHBOARD._serialized_start=653
  _NEWRELICAPPLICATIONENTITYASSETMODEL_APMDASHBOARD._serialized_end=831
  _NEWRELICAPPLICATIONENTITYASSETOPTIONS._serialized_start=833
  _NEWRELICAPPLICATIONENTITYASSETOPTIONS._serialized_end=899
  _NEWRELICDASHBOARDENTITYASSETMODEL._serialized_start=902
  _NEWRELICDASHBOARDENTITYASSETMODEL._serialized_end=1555
  _NEWRELICDASHBOARDENTITYASSETMODEL_PAGEWIDGET._serialized_start=1131
  _NEWRELICDASHBOARDENTITYASSETMODEL_PAGEWIDGET._serialized_end=1357
  _NEWRELICDASHBOARDENTITYASSETMODEL_DASHBOARDPAGE._serialized_start=1360
  _NEWRELICDASHBOARDENTITYASSETMODEL_DASHBOARDPAGE._serialized_end=1555
  _NEWRELICDASHBOARDENTITYASSETOPTIONS._serialized_start=1558
  _NEWRELICDASHBOARDENTITYASSETOPTIONS._serialized_end=2055
  _NEWRELICDASHBOARDENTITYASSETOPTIONS_DASHBOARDOPTIONS._serialized_start=1691
  _NEWRELICDASHBOARDENTITYASSETOPTIONS_DASHBOARDOPTIONS._serialized_end=2055
  _NEWRELICDASHBOARDENTITYASSETOPTIONS_DASHBOARDOPTIONS_DASHBOARDPAGEOPTIONS._serialized_start=1935
  _NEWRELICDASHBOARDENTITYASSETOPTIONS_DASHBOARDOPTIONS_DASHBOARDPAGEOPTIONS._serialized_end=2055
  _NEWRELICDASHBOARDENTITYASSETMODELV2._serialized_start=2058
  _NEWRELICDASHBOARDENTITYASSETMODELV2._serialized_end=2726
  _NEWRELICDASHBOARDENTITYASSETMODELV2_PAGEWIDGETV2._serialized_start=2293
  _NEWRELICDASHBOARDENTITYASSETMODELV2_PAGEWIDGETV2._serialized_end=2522
  _NEWRELICDASHBOARDENTITYASSETMODELV2_DASHBOARDPAGEV2._serialized_start=2525
  _NEWRELICDASHBOARDENTITYASSETMODELV2_DASHBOARDPAGEV2._serialized_end=2726
  _NEWRELICDASHBOARDENTITYASSETOPTIONSV2._serialized_start=2729
  _NEWRELICDASHBOARDENTITYASSETOPTIONSV2._serialized_end=3242
  _NEWRELICDASHBOARDENTITYASSETOPTIONSV2_DASHBOARDOPTIONSV2._serialized_start=2868
  _NEWRELICDASHBOARDENTITYASSETOPTIONSV2_DASHBOARDOPTIONSV2._serialized_end=3242
  _NEWRELICDASHBOARDENTITYASSETOPTIONSV2_DASHBOARDOPTIONSV2_DASHBOARDPAGEOPTIONSV2._serialized_start=3120
  _NEWRELICDASHBOARDENTITYASSETOPTIONSV2_DASHBOARDOPTIONSV2_DASHBOARDPAGEOPTIONSV2._serialized_end=3242
  _NEWRELICASSETMODEL._serialized_start=3245
  _NEWRELICASSETMODEL._serialized_end=3702
  _NEWRELICASSETS._serialized_start=3704
  _NEWRELICASSETS._serialized_end=3775
# @@protoc_insertion_point(module_scope)
