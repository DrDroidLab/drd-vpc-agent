from typing import Dict

from google.protobuf.json_format import MessageToJson, Parse, MessageToDict, ParseDict
from google.protobuf.message import Message
from google.protobuf.wrappers_pb2 import BoolValue, UInt32Value

from drdroid_debug_toolkit.core.protos.base_pb2 import TimeRange, Page, Meta


class ProtoException(ValueError):
    pass


def proto_to_json(obj: Message, use_snake_case: bool = True) -> str:
    if not obj:
        raise ProtoException('Trying to serialize None obj')
    try:
        text = MessageToJson(obj, preserving_proto_field_name=use_snake_case)
    except Exception as e:
        raise ProtoException(f'Error serializing proto message: {e}')
    return text


def proto_to_dict(obj: Message, use_snake_case: bool = True) -> Dict:
    if not obj:
        raise ProtoException('Trying to serialize None obj')
    try:
        message_dict = MessageToDict(obj, preserving_proto_field_name=use_snake_case)
    except Exception as e:
        raise ProtoException(f'Error converting proto message to dict: {e}')
    return message_dict


def json_to_proto(text: str, proto_clazz, ignore_unknown_fields=True) -> Message:
    if proto_clazz:
        msg = proto_clazz()
    else:
        raise ProtoException('No message class defined')

    try:
        msg = Parse(text, msg, ignore_unknown_fields)
    except Exception as e:
        raise ProtoException(f'Error while parsing text: {e}')
    return msg


def dict_to_proto(d: Dict, proto_clazz, ignore_unknown_fields=True) -> Message:
    if proto_clazz:
        msg = proto_clazz()
    else:
        raise ProtoException('No message class defined')

    try:
        msg = ParseDict(d, msg, ignore_unknown_fields)
    except Exception as e:
        raise ProtoException(f'Error while parsing text: {e}')
    return msg


def get_meta(tr: TimeRange = TimeRange(), page: Page = Page(), total_count: int = 0,
             show_inactive: BoolValue = BoolValue(value=False)):
    return Meta(time_range=tr, page=page, total_count=UInt32Value(value=total_count), show_inactive=show_inactive)
