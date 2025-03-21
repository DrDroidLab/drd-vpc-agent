"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import collections.abc
import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message
import google.protobuf.wrappers_pb2
import protos.literal_pb2
import sys
import typing

if sys.version_info >= (3, 10):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

class _FormFieldType:
    ValueType = typing.NewType("ValueType", builtins.int)
    V: typing_extensions.TypeAlias = ValueType

class _FormFieldTypeEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[_FormFieldType.ValueType], builtins.type):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    UNKNOWN_FT: _FormFieldType.ValueType  # 0
    TEXT_FT: _FormFieldType.ValueType  # 1
    MULTILINE_FT: _FormFieldType.ValueType  # 2
    BUTTON_FT: _FormFieldType.ValueType  # 3
    IFRAME_RENDER_FT: _FormFieldType.ValueType  # 4
    DROPDOWN_FT: _FormFieldType.ValueType  # 5
    TYPING_DROPDOWN_FT: _FormFieldType.ValueType  # 6
    TYPING_DROPDOWN_MULTIPLE_FT: _FormFieldType.ValueType  # 7
    WYSIWYG_FT: _FormFieldType.ValueType  # 8
    COMPOSITE_FT: _FormFieldType.ValueType  # 9
    STRING_ARRAY_FT: _FormFieldType.ValueType  # 10
    DATE_FT: _FormFieldType.ValueType  # 11
    CHECKBOX_FT: _FormFieldType.ValueType  # 12
    CODE_EDITOR_FT: _FormFieldType.ValueType  # 13

class FormFieldType(_FormFieldType, metaclass=_FormFieldTypeEnumTypeWrapper): ...

UNKNOWN_FT: FormFieldType.ValueType  # 0
TEXT_FT: FormFieldType.ValueType  # 1
MULTILINE_FT: FormFieldType.ValueType  # 2
BUTTON_FT: FormFieldType.ValueType  # 3
IFRAME_RENDER_FT: FormFieldType.ValueType  # 4
DROPDOWN_FT: FormFieldType.ValueType  # 5
TYPING_DROPDOWN_FT: FormFieldType.ValueType  # 6
TYPING_DROPDOWN_MULTIPLE_FT: FormFieldType.ValueType  # 7
WYSIWYG_FT: FormFieldType.ValueType  # 8
COMPOSITE_FT: FormFieldType.ValueType  # 9
STRING_ARRAY_FT: FormFieldType.ValueType  # 10
DATE_FT: FormFieldType.ValueType  # 11
CHECKBOX_FT: FormFieldType.ValueType  # 12
CODE_EDITOR_FT: FormFieldType.ValueType  # 13
global___FormFieldType = FormFieldType

@typing_extensions.final
class FormField(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    KEY_NAME_FIELD_NUMBER: builtins.int
    DISPLAY_NAME_FIELD_NUMBER: builtins.int
    DESCRIPTION_FIELD_NUMBER: builtins.int
    DATA_TYPE_FIELD_NUMBER: builtins.int
    IS_OPTIONAL_FIELD_NUMBER: builtins.int
    DEFAULT_VALUE_FIELD_NUMBER: builtins.int
    VALID_VALUES_FIELD_NUMBER: builtins.int
    IS_COMPOSITE_FIELD_NUMBER: builtins.int
    COMPOSITE_FIELDS_FIELD_NUMBER: builtins.int
    MAX_LENGTH_ALLOWED_FIELD_NUMBER: builtins.int
    IS_DATE_TIME_FIELD_FIELD_NUMBER: builtins.int
    FORM_FIELD_TYPE_FIELD_NUMBER: builtins.int
    DISABLED_FIELD_NUMBER: builtins.int
    @property
    def key_name(self) -> google.protobuf.wrappers_pb2.StringValue: ...
    @property
    def display_name(self) -> google.protobuf.wrappers_pb2.StringValue: ...
    @property
    def description(self) -> google.protobuf.wrappers_pb2.StringValue: ...
    data_type: protos.literal_pb2.LiteralType.ValueType
    is_optional: builtins.bool
    @property
    def default_value(self) -> protos.literal_pb2.Literal: ...
    @property
    def valid_values(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[protos.literal_pb2.Literal]: ...
    is_composite: builtins.bool
    @property
    def composite_fields(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___FormField]: ...
    @property
    def max_length_allowed(self) -> google.protobuf.wrappers_pb2.UInt64Value: ...
    is_date_time_field: builtins.bool
    form_field_type: global___FormFieldType.ValueType
    disabled: builtins.bool
    def __init__(
        self,
        *,
        key_name: google.protobuf.wrappers_pb2.StringValue | None = ...,
        display_name: google.protobuf.wrappers_pb2.StringValue | None = ...,
        description: google.protobuf.wrappers_pb2.StringValue | None = ...,
        data_type: protos.literal_pb2.LiteralType.ValueType = ...,
        is_optional: builtins.bool = ...,
        default_value: protos.literal_pb2.Literal | None = ...,
        valid_values: collections.abc.Iterable[protos.literal_pb2.Literal] | None = ...,
        is_composite: builtins.bool = ...,
        composite_fields: collections.abc.Iterable[global___FormField] | None = ...,
        max_length_allowed: google.protobuf.wrappers_pb2.UInt64Value | None = ...,
        is_date_time_field: builtins.bool = ...,
        form_field_type: global___FormFieldType.ValueType = ...,
        disabled: builtins.bool = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["default_value", b"default_value", "description", b"description", "display_name", b"display_name", "key_name", b"key_name", "max_length_allowed", b"max_length_allowed"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["composite_fields", b"composite_fields", "data_type", b"data_type", "default_value", b"default_value", "description", b"description", "disabled", b"disabled", "display_name", b"display_name", "form_field_type", b"form_field_type", "is_composite", b"is_composite", "is_date_time_field", b"is_date_time_field", "is_optional", b"is_optional", "key_name", b"key_name", "max_length_allowed", b"max_length_allowed", "valid_values", b"valid_values"]) -> None: ...

global___FormField = FormField
