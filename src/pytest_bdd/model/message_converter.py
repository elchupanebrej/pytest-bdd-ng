from cucumber_messages import json_converter

from . import message_extension

message_converter: json_converter.JsonDataclassConverter = json_converter.JsonDataclassConverter(
    module_scope=message_extension
)
