# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/assets/asset.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from protos import base_pb2 as protos_dot_base__pb2
from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2
from google.protobuf import struct_pb2 as google_dot_protobuf_dot_struct__pb2
from protos.connectors import connector_pb2 as protos_dot_connectors_dot_connector__pb2
from protos.assets import cloudwatch_asset_pb2 as protos_dot_assets_dot_cloudwatch__asset__pb2
from protos.assets import grafana_asset_pb2 as protos_dot_assets_dot_grafana__asset__pb2
from protos.assets import clickhouse_asset_pb2 as protos_dot_assets_dot_clickhouse__asset__pb2
from protos.assets import slack_asset_pb2 as protos_dot_assets_dot_slack__asset__pb2
from protos.assets import newrelic_asset_pb2 as protos_dot_assets_dot_newrelic__asset__pb2
from protos.assets import datadog_asset_pb2 as protos_dot_assets_dot_datadog__asset__pb2
from protos.assets import postgres_asset_pb2 as protos_dot_assets_dot_postgres__asset__pb2
from protos.assets import eks_asset_pb2 as protos_dot_assets_dot_eks__asset__pb2
from protos.assets import azure_asset_pb2 as protos_dot_assets_dot_azure__asset__pb2
from protos.assets import bash_asset_pb2 as protos_dot_assets_dot_bash__asset__pb2
from protos.assets import gke_asset_pb2 as protos_dot_assets_dot_gke__asset__pb2
from protos.assets import elastic_search_asset_pb2 as protos_dot_assets_dot_elastic__search__asset__pb2
from protos.assets import gcm_asset_pb2 as protos_dot_assets_dot_gcm__asset__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x19protos/assets/asset.proto\x12\x11protos.connectors\x1a\x11protos/base.proto\x1a\x1egoogle/protobuf/wrappers.proto\x1a\x1cgoogle/protobuf/struct.proto\x1a!protos/connectors/connector.proto\x1a$protos/assets/cloudwatch_asset.proto\x1a!protos/assets/grafana_asset.proto\x1a$protos/assets/clickhouse_asset.proto\x1a\x1fprotos/assets/slack_asset.proto\x1a\"protos/assets/newrelic_asset.proto\x1a!protos/assets/datadog_asset.proto\x1a\"protos/assets/postgres_asset.proto\x1a\x1dprotos/assets/eks_asset.proto\x1a\x1fprotos/assets/azure_asset.proto\x1a\x1eprotos/assets/bash_asset.proto\x1a\x1dprotos/assets/gke_asset.proto\x1a(protos/assets/elastic_search_asset.proto\x1a\x1dprotos/assets/gcm_asset.proto\"\xfc\x05\n\x16\x41\x63\x63ountConnectorAssets\x12/\n\tconnector\x18\x01 \x01(\x0b\x32\x1c.protos.connectors.Connector\x12\x39\n\ncloudwatch\x18\x65 \x01(\x0b\x32#.protos.connectors.CloudwatchAssetsH\x00\x12\x33\n\x07grafana\x18\x66 \x01(\x0b\x32 .protos.connectors.GrafanaAssetsH\x00\x12\x39\n\nclickhouse\x18g \x01(\x0b\x32#.protos.connectors.ClickhouseAssetsH\x00\x12/\n\x05slack\x18h \x01(\x0b\x32\x1e.protos.connectors.SlackAssetsH\x00\x12\x36\n\tnew_relic\x18i \x01(\x0b\x32!.protos.connectors.NewRelicAssetsH\x00\x12\x33\n\x07\x64\x61tadog\x18j \x01(\x0b\x32 .protos.connectors.DatadogAssetsH\x00\x12\x35\n\x08postgres\x18k \x01(\x0b\x32!.protos.connectors.PostgresAssetsH\x00\x12+\n\x03\x65ks\x18l \x01(\x0b\x32\x1c.protos.connectors.EksAssetsH\x00\x12-\n\x04\x62\x61sh\x18m \x01(\x0b\x32\x1d.protos.connectors.BashAssetsH\x00\x12/\n\x05\x61zure\x18n \x01(\x0b\x32\x1e.protos.connectors.AzureAssetsH\x00\x12+\n\x03gke\x18o \x01(\x0b\x32\x1c.protos.connectors.GkeAssetsH\x00\x12@\n\x0e\x65lastic_search\x18p \x01(\x0b\x32&.protos.connectors.ElasticSearchAssetsH\x00\x12+\n\x03gcm\x18q \x01(\x0b\x32\x1c.protos.connectors.GcmAssetsH\x00\x42\x08\n\x06\x61ssetsb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.assets.asset_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _ACCOUNTCONNECTORASSETS._serialized_start=616
  _ACCOUNTCONNECTORASSETS._serialized_end=1380
# @@protoc_insertion_point(module_scope)
