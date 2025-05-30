# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/assets/gcm_asset.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2
from protos import base_pb2 as protos_dot_base__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1dprotos/assets/gcm_asset.proto\x12\x11protos.connectors\x1a\x1egoogle/protobuf/wrappers.proto\x1a\x11protos/base.proto\"\xfd\x01\n\x13GcmMetricAssetModel\x12\x31\n\x0bmetric_type\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12R\n\x16label_value_metric_map\x18\x02 \x03(\x0b\x32\x32.protos.connectors.GcmMetricAssetModel.MetricLabel\x1a_\n\x0bMetricLabel\x12*\n\x04name\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x13\n\x0b\x64\x65scription\x18\x02 \x03(\t\x12\x0f\n\x07metrics\x18\x03 \x03(\t\"-\n\x15GcmMetricAssetOptions\x12\x14\n\x0cmetric_types\x18\x01 \x03(\t\"\xb9\x03\n\x1cGcmDashboardEntityAssetModel\x12\x32\n\x0c\x64\x61shboard_id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x34\n\x0e\x64\x61shboard_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12P\n\x07widgets\x18\x03 \x03(\x0b\x32?.protos.connectors.GcmDashboardEntityAssetModel.DashboardWidget\x1a\xdc\x01\n\x0f\x44\x61shboardWidget\x12/\n\twidget_id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x31\n\x0bwidget_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x31\n\x0bwidget_type\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x32\n\x0cwidget_query\x18\x04 \x01(\x0b\x32\x1c.google.protobuf.StringValue\"\x8d\x02\n\x1eGcmDashboardEntityAssetOptions\x12V\n\ndashboards\x18\x01 \x03(\x0b\x32\x42.protos.connectors.GcmDashboardEntityAssetOptions.DashboardOptions\x1a\x92\x01\n\x10\x44\x61shboardOptions\x12\x32\n\x0c\x64\x61shboard_id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x34\n\x0e\x64\x61shboard_name\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x14\n\x0cwidget_names\x18\x03 \x03(\t\"\xfc\x02\n\x1cGcmCloudRunServiceAssetModel\x12\x32\n\x0cservice_name\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12,\n\x06region\x18\x02 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x30\n\nproject_id\x18\x03 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12O\n\x07metrics\x18\x04 \x03(\x0b\x32>.protos.connectors.GcmCloudRunServiceAssetModel.CloudRunMetric\x1aw\n\x0e\x43loudRunMetric\x12\x31\n\x0bmetric_name\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12\x32\n\x0c\x61ggregations\x18\x02 \x03(\x0b\x32\x1c.google.protobuf.StringValue\"H\n\x1eGcmCloudRunServiceAssetOptions\x12\x15\n\rservice_names\x18\x01 \x03(\t\x12\x0f\n\x07regions\x18\x02 \x03(\t\"\x8b\x03\n\rGcmAssetModel\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12&\n\x0e\x63onnector_type\x18\x02 \x01(\x0e\x32\x0e.protos.Source\x12%\n\x04type\x18\x03 \x01(\x0e\x32\x17.protos.SourceModelType\x12\x14\n\x0clast_updated\x18\x04 \x01(\x10\x12<\n\ngcm_metric\x18\x06 \x01(\x0b\x32&.protos.connectors.GcmMetricAssetModelH\x00\x12H\n\rgcm_dashboard\x18\x07 \x01(\x0b\x32/.protos.connectors.GcmDashboardEntityAssetModelH\x00\x12Z\n\x1fgcm_cloud_run_service_dashboard\x18\x08 \x01(\x0b\x32/.protos.connectors.GcmCloudRunServiceAssetModelH\x00\x42\x07\n\x05\x61sset\"=\n\tGcmAssets\x12\x30\n\x06\x61ssets\x18\x01 \x03(\x0b\x32 .protos.connectors.GcmAssetModelb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.assets.gcm_asset_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _GCMMETRICASSETMODEL._serialized_start=104
  _GCMMETRICASSETMODEL._serialized_end=357
  _GCMMETRICASSETMODEL_METRICLABEL._serialized_start=262
  _GCMMETRICASSETMODEL_METRICLABEL._serialized_end=357
  _GCMMETRICASSETOPTIONS._serialized_start=359
  _GCMMETRICASSETOPTIONS._serialized_end=404
  _GCMDASHBOARDENTITYASSETMODEL._serialized_start=407
  _GCMDASHBOARDENTITYASSETMODEL._serialized_end=848
  _GCMDASHBOARDENTITYASSETMODEL_DASHBOARDWIDGET._serialized_start=628
  _GCMDASHBOARDENTITYASSETMODEL_DASHBOARDWIDGET._serialized_end=848
  _GCMDASHBOARDENTITYASSETOPTIONS._serialized_start=851
  _GCMDASHBOARDENTITYASSETOPTIONS._serialized_end=1120
  _GCMDASHBOARDENTITYASSETOPTIONS_DASHBOARDOPTIONS._serialized_start=974
  _GCMDASHBOARDENTITYASSETOPTIONS_DASHBOARDOPTIONS._serialized_end=1120
  _GCMCLOUDRUNSERVICEASSETMODEL._serialized_start=1123
  _GCMCLOUDRUNSERVICEASSETMODEL._serialized_end=1503
  _GCMCLOUDRUNSERVICEASSETMODEL_CLOUDRUNMETRIC._serialized_start=1384
  _GCMCLOUDRUNSERVICEASSETMODEL_CLOUDRUNMETRIC._serialized_end=1503
  _GCMCLOUDRUNSERVICEASSETOPTIONS._serialized_start=1505
  _GCMCLOUDRUNSERVICEASSETOPTIONS._serialized_end=1577
  _GCMASSETMODEL._serialized_start=1580
  _GCMASSETMODEL._serialized_end=1975
  _GCMASSETS._serialized_start=1977
  _GCMASSETS._serialized_end=2038
# @@protoc_insertion_point(module_scope)
