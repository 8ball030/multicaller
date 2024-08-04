# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: positions.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0fpositions.proto\x12 aea.eightballer.positions.v0_1_0\"\xb1\x14\n\x10PositionsMessage\x12\x66\n\rall_positions\x18\x05 \x01(\x0b\x32M.aea.eightballer.positions.v0_1_0.PositionsMessage.All_Positions_PerformativeH\x00\x12V\n\x05\x65rror\x18\x06 \x01(\x0b\x32\x45.aea.eightballer.positions.v0_1_0.PositionsMessage.Error_PerformativeH\x00\x12n\n\x11get_all_positions\x18\x07 \x01(\x0b\x32Q.aea.eightballer.positions.v0_1_0.PositionsMessage.Get_All_Positions_PerformativeH\x00\x12\x64\n\x0cget_position\x18\x08 \x01(\x0b\x32L.aea.eightballer.positions.v0_1_0.PositionsMessage.Get_Position_PerformativeH\x00\x12\\\n\x08position\x18\t \x01(\x0b\x32H.aea.eightballer.positions.v0_1_0.PositionsMessage.Position_PerformativeH\x00\x1a\xb7\x01\n\tErrorCode\x12^\n\nerror_code\x18\x01 \x01(\x0e\x32J.aea.eightballer.positions.v0_1_0.PositionsMessage.ErrorCode.ErrorCodeEnum\"J\n\rErrorCodeEnum\x12\x14\n\x10UNKNOWN_EXCHANGE\x10\x00\x12\x14\n\x10UNKNOWN_POSITION\x10\x01\x12\r\n\tAPI_ERROR\x10\x02\x1a\x9f\x05\n\x08Position\x1a\x92\x05\n\x08Position\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0e\n\x06symbol\x18\x02 \x01(\t\x12\x11\n\ttimestamp\x18\x03 \x01(\x03\x12\x10\n\x08\x64\x61tetime\x18\x04 \x01(\t\x12\x1b\n\x13lastUpdateTimestamp\x18\x05 \x01(\x03\x12\x15\n\rinitialMargin\x18\x06 \x01(\x02\x12\x1f\n\x17initialMarginPercentage\x18\x07 \x01(\x02\x12\x19\n\x11maintenanceMargin\x18\x08 \x01(\x02\x12#\n\x1bmaintenanceMarginPercentage\x18\t \x01(\x02\x12\x12\n\nentryPrice\x18\n \x01(\x02\x12\x10\n\x08notional\x18\x0b \x01(\x02\x12\x10\n\x08leverage\x18\x0c \x01(\x02\x12\x15\n\runrealizedPnl\x18\r \x01(\x02\x12\x11\n\tcontracts\x18\x0e \x01(\x02\x12\x14\n\x0c\x63ontractSize\x18\x0f \x01(\x02\x12\x13\n\x0bmarginRatio\x18\x10 \x01(\x02\x12\x18\n\x10liquidationPrice\x18\x11 \x01(\x02\x12\x11\n\tmarkPrice\x18\x12 \x01(\x02\x12\x11\n\tlastPrice\x18\x13 \x01(\x02\x12\x12\n\ncollateral\x18\x14 \x01(\x02\x12\x12\n\nmarginMode\x18\x15 \x01(\t\x12M\n\x04side\x18\x16 \x01(\x0b\x32?.aea.eightballer.positions.v0_1_0.PositionsMessage.PositionSide\x12\x12\n\npercentage\x18\x17 \x01(\x02\x12\x0c\n\x04info\x18\x18 \x01(\t\x12\x0c\n\x04size\x18\x19 \x01(\x02\x12\x13\n\x0b\x65xchange_id\x18\x1a \x01(\t\x12\x0e\n\x06hedged\x18\x1b \x01(\t\x12\x17\n\x0fstop_loss_price\x18\x1c \x01(\x02\x1a\xa0\x01\n\x0cPositionSide\x12g\n\rposition_side\x18\x01 \x01(\x0e\x32P.aea.eightballer.positions.v0_1_0.PositionsMessage.PositionSide.PositionSideEnum\"\'\n\x10PositionSideEnum\x12\x08\n\x04LONG\x10\x00\x12\t\n\x05SHORT\x10\x01\x1ah\n\tPositions\x1a[\n\tPositions\x12N\n\tpositions\x18\x01 \x03(\x0b\x32;.aea.eightballer.positions.v0_1_0.PositionsMessage.Position\x1a\xce\x02\n\x1eGet_All_Positions_Performative\x12\x13\n\x0b\x65xchange_id\x18\x01 \x01(\t\x12m\n\x06params\x18\x02 \x03(\x0b\x32].aea.eightballer.positions.v0_1_0.PositionsMessage.Get_All_Positions_Performative.ParamsEntry\x12\x15\n\rparams_is_set\x18\x03 \x01(\x08\x12M\n\x04side\x18\x04 \x01(\x0b\x32?.aea.eightballer.positions.v0_1_0.PositionsMessage.PositionSide\x12\x13\n\x0bside_is_set\x18\x05 \x01(\x08\x1a-\n\x0bParamsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\x0c:\x02\x38\x01\x1a\x45\n\x19Get_Position_Performative\x12\x13\n\x0bposition_id\x18\x01 \x01(\t\x12\x13\n\x0b\x65xchange_id\x18\x02 \x01(\t\x1a\x82\x01\n\x1a\x41ll_Positions_Performative\x12O\n\tpositions\x18\x01 \x01(\x0b\x32<.aea.eightballer.positions.v0_1_0.PositionsMessage.Positions\x12\x13\n\x0b\x65xchange_id\x18\x02 \x01(\t\x1a{\n\x15Position_Performative\x12M\n\x08position\x18\x01 \x01(\x0b\x32;.aea.eightballer.positions.v0_1_0.PositionsMessage.Position\x12\x13\n\x0b\x65xchange_id\x18\x02 \x01(\t\x1a\x95\x02\n\x12\x45rror_Performative\x12P\n\nerror_code\x18\x01 \x01(\x0b\x32<.aea.eightballer.positions.v0_1_0.PositionsMessage.ErrorCode\x12\x11\n\terror_msg\x18\x02 \x01(\t\x12h\n\nerror_data\x18\x03 \x03(\x0b\x32T.aea.eightballer.positions.v0_1_0.PositionsMessage.Error_Performative.ErrorDataEntry\x1a\x30\n\x0e\x45rrorDataEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\x0c:\x02\x38\x01\x42\x0e\n\x0cperformativeb\x06proto3')



_POSITIONSMESSAGE = DESCRIPTOR.message_types_by_name['PositionsMessage']
_POSITIONSMESSAGE_ERRORCODE = _POSITIONSMESSAGE.nested_types_by_name['ErrorCode']
_POSITIONSMESSAGE_POSITION = _POSITIONSMESSAGE.nested_types_by_name['Position']
_POSITIONSMESSAGE_POSITION_POSITION = _POSITIONSMESSAGE_POSITION.nested_types_by_name['Position']
_POSITIONSMESSAGE_POSITIONSIDE = _POSITIONSMESSAGE.nested_types_by_name['PositionSide']
_POSITIONSMESSAGE_POSITIONS = _POSITIONSMESSAGE.nested_types_by_name['Positions']
_POSITIONSMESSAGE_POSITIONS_POSITIONS = _POSITIONSMESSAGE_POSITIONS.nested_types_by_name['Positions']
_POSITIONSMESSAGE_GET_ALL_POSITIONS_PERFORMATIVE = _POSITIONSMESSAGE.nested_types_by_name['Get_All_Positions_Performative']
_POSITIONSMESSAGE_GET_ALL_POSITIONS_PERFORMATIVE_PARAMSENTRY = _POSITIONSMESSAGE_GET_ALL_POSITIONS_PERFORMATIVE.nested_types_by_name['ParamsEntry']
_POSITIONSMESSAGE_GET_POSITION_PERFORMATIVE = _POSITIONSMESSAGE.nested_types_by_name['Get_Position_Performative']
_POSITIONSMESSAGE_ALL_POSITIONS_PERFORMATIVE = _POSITIONSMESSAGE.nested_types_by_name['All_Positions_Performative']
_POSITIONSMESSAGE_POSITION_PERFORMATIVE = _POSITIONSMESSAGE.nested_types_by_name['Position_Performative']
_POSITIONSMESSAGE_ERROR_PERFORMATIVE = _POSITIONSMESSAGE.nested_types_by_name['Error_Performative']
_POSITIONSMESSAGE_ERROR_PERFORMATIVE_ERRORDATAENTRY = _POSITIONSMESSAGE_ERROR_PERFORMATIVE.nested_types_by_name['ErrorDataEntry']
_POSITIONSMESSAGE_ERRORCODE_ERRORCODEENUM = _POSITIONSMESSAGE_ERRORCODE.enum_types_by_name['ErrorCodeEnum']
_POSITIONSMESSAGE_POSITIONSIDE_POSITIONSIDEENUM = _POSITIONSMESSAGE_POSITIONSIDE.enum_types_by_name['PositionSideEnum']
PositionsMessage = _reflection.GeneratedProtocolMessageType('PositionsMessage', (_message.Message,), {

  'ErrorCode' : _reflection.GeneratedProtocolMessageType('ErrorCode', (_message.Message,), {
    'DESCRIPTOR' : _POSITIONSMESSAGE_ERRORCODE,
    '__module__' : 'positions_pb2'
    # @@protoc_insertion_point(class_scope:aea.eightballer.positions.v0_1_0.PositionsMessage.ErrorCode)
    })
  ,

  'Position' : _reflection.GeneratedProtocolMessageType('Position', (_message.Message,), {

    'Position' : _reflection.GeneratedProtocolMessageType('Position', (_message.Message,), {
      'DESCRIPTOR' : _POSITIONSMESSAGE_POSITION_POSITION,
      '__module__' : 'positions_pb2'
      # @@protoc_insertion_point(class_scope:aea.eightballer.positions.v0_1_0.PositionsMessage.Position.Position)
      })
    ,
    'DESCRIPTOR' : _POSITIONSMESSAGE_POSITION,
    '__module__' : 'positions_pb2'
    # @@protoc_insertion_point(class_scope:aea.eightballer.positions.v0_1_0.PositionsMessage.Position)
    })
  ,

  'PositionSide' : _reflection.GeneratedProtocolMessageType('PositionSide', (_message.Message,), {
    'DESCRIPTOR' : _POSITIONSMESSAGE_POSITIONSIDE,
    '__module__' : 'positions_pb2'
    # @@protoc_insertion_point(class_scope:aea.eightballer.positions.v0_1_0.PositionsMessage.PositionSide)
    })
  ,

  'Positions' : _reflection.GeneratedProtocolMessageType('Positions', (_message.Message,), {

    'Positions' : _reflection.GeneratedProtocolMessageType('Positions', (_message.Message,), {
      'DESCRIPTOR' : _POSITIONSMESSAGE_POSITIONS_POSITIONS,
      '__module__' : 'positions_pb2'
      # @@protoc_insertion_point(class_scope:aea.eightballer.positions.v0_1_0.PositionsMessage.Positions.Positions)
      })
    ,
    'DESCRIPTOR' : _POSITIONSMESSAGE_POSITIONS,
    '__module__' : 'positions_pb2'
    # @@protoc_insertion_point(class_scope:aea.eightballer.positions.v0_1_0.PositionsMessage.Positions)
    })
  ,

  'Get_All_Positions_Performative' : _reflection.GeneratedProtocolMessageType('Get_All_Positions_Performative', (_message.Message,), {

    'ParamsEntry' : _reflection.GeneratedProtocolMessageType('ParamsEntry', (_message.Message,), {
      'DESCRIPTOR' : _POSITIONSMESSAGE_GET_ALL_POSITIONS_PERFORMATIVE_PARAMSENTRY,
      '__module__' : 'positions_pb2'
      # @@protoc_insertion_point(class_scope:aea.eightballer.positions.v0_1_0.PositionsMessage.Get_All_Positions_Performative.ParamsEntry)
      })
    ,
    'DESCRIPTOR' : _POSITIONSMESSAGE_GET_ALL_POSITIONS_PERFORMATIVE,
    '__module__' : 'positions_pb2'
    # @@protoc_insertion_point(class_scope:aea.eightballer.positions.v0_1_0.PositionsMessage.Get_All_Positions_Performative)
    })
  ,

  'Get_Position_Performative' : _reflection.GeneratedProtocolMessageType('Get_Position_Performative', (_message.Message,), {
    'DESCRIPTOR' : _POSITIONSMESSAGE_GET_POSITION_PERFORMATIVE,
    '__module__' : 'positions_pb2'
    # @@protoc_insertion_point(class_scope:aea.eightballer.positions.v0_1_0.PositionsMessage.Get_Position_Performative)
    })
  ,

  'All_Positions_Performative' : _reflection.GeneratedProtocolMessageType('All_Positions_Performative', (_message.Message,), {
    'DESCRIPTOR' : _POSITIONSMESSAGE_ALL_POSITIONS_PERFORMATIVE,
    '__module__' : 'positions_pb2'
    # @@protoc_insertion_point(class_scope:aea.eightballer.positions.v0_1_0.PositionsMessage.All_Positions_Performative)
    })
  ,

  'Position_Performative' : _reflection.GeneratedProtocolMessageType('Position_Performative', (_message.Message,), {
    'DESCRIPTOR' : _POSITIONSMESSAGE_POSITION_PERFORMATIVE,
    '__module__' : 'positions_pb2'
    # @@protoc_insertion_point(class_scope:aea.eightballer.positions.v0_1_0.PositionsMessage.Position_Performative)
    })
  ,

  'Error_Performative' : _reflection.GeneratedProtocolMessageType('Error_Performative', (_message.Message,), {

    'ErrorDataEntry' : _reflection.GeneratedProtocolMessageType('ErrorDataEntry', (_message.Message,), {
      'DESCRIPTOR' : _POSITIONSMESSAGE_ERROR_PERFORMATIVE_ERRORDATAENTRY,
      '__module__' : 'positions_pb2'
      # @@protoc_insertion_point(class_scope:aea.eightballer.positions.v0_1_0.PositionsMessage.Error_Performative.ErrorDataEntry)
      })
    ,
    'DESCRIPTOR' : _POSITIONSMESSAGE_ERROR_PERFORMATIVE,
    '__module__' : 'positions_pb2'
    # @@protoc_insertion_point(class_scope:aea.eightballer.positions.v0_1_0.PositionsMessage.Error_Performative)
    })
  ,
  'DESCRIPTOR' : _POSITIONSMESSAGE,
  '__module__' : 'positions_pb2'
  # @@protoc_insertion_point(class_scope:aea.eightballer.positions.v0_1_0.PositionsMessage)
  })
_sym_db.RegisterMessage(PositionsMessage)
_sym_db.RegisterMessage(PositionsMessage.ErrorCode)
_sym_db.RegisterMessage(PositionsMessage.Position)
_sym_db.RegisterMessage(PositionsMessage.Position.Position)
_sym_db.RegisterMessage(PositionsMessage.PositionSide)
_sym_db.RegisterMessage(PositionsMessage.Positions)
_sym_db.RegisterMessage(PositionsMessage.Positions.Positions)
_sym_db.RegisterMessage(PositionsMessage.Get_All_Positions_Performative)
_sym_db.RegisterMessage(PositionsMessage.Get_All_Positions_Performative.ParamsEntry)
_sym_db.RegisterMessage(PositionsMessage.Get_Position_Performative)
_sym_db.RegisterMessage(PositionsMessage.All_Positions_Performative)
_sym_db.RegisterMessage(PositionsMessage.Position_Performative)
_sym_db.RegisterMessage(PositionsMessage.Error_Performative)
_sym_db.RegisterMessage(PositionsMessage.Error_Performative.ErrorDataEntry)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _POSITIONSMESSAGE_GET_ALL_POSITIONS_PERFORMATIVE_PARAMSENTRY._options = None
  _POSITIONSMESSAGE_GET_ALL_POSITIONS_PERFORMATIVE_PARAMSENTRY._serialized_options = b'8\001'
  _POSITIONSMESSAGE_ERROR_PERFORMATIVE_ERRORDATAENTRY._options = None
  _POSITIONSMESSAGE_ERROR_PERFORMATIVE_ERRORDATAENTRY._serialized_options = b'8\001'
  _POSITIONSMESSAGE._serialized_start=54
  _POSITIONSMESSAGE._serialized_end=2663
  _POSITIONSMESSAGE_ERRORCODE._serialized_start=575
  _POSITIONSMESSAGE_ERRORCODE._serialized_end=758
  _POSITIONSMESSAGE_ERRORCODE_ERRORCODEENUM._serialized_start=684
  _POSITIONSMESSAGE_ERRORCODE_ERRORCODEENUM._serialized_end=758
  _POSITIONSMESSAGE_POSITION._serialized_start=761
  _POSITIONSMESSAGE_POSITION._serialized_end=1432
  _POSITIONSMESSAGE_POSITION_POSITION._serialized_start=774
  _POSITIONSMESSAGE_POSITION_POSITION._serialized_end=1432
  _POSITIONSMESSAGE_POSITIONSIDE._serialized_start=1435
  _POSITIONSMESSAGE_POSITIONSIDE._serialized_end=1595
  _POSITIONSMESSAGE_POSITIONSIDE_POSITIONSIDEENUM._serialized_start=1556
  _POSITIONSMESSAGE_POSITIONSIDE_POSITIONSIDEENUM._serialized_end=1595
  _POSITIONSMESSAGE_POSITIONS._serialized_start=1597
  _POSITIONSMESSAGE_POSITIONS._serialized_end=1701
  _POSITIONSMESSAGE_POSITIONS_POSITIONS._serialized_start=1610
  _POSITIONSMESSAGE_POSITIONS_POSITIONS._serialized_end=1701
  _POSITIONSMESSAGE_GET_ALL_POSITIONS_PERFORMATIVE._serialized_start=1704
  _POSITIONSMESSAGE_GET_ALL_POSITIONS_PERFORMATIVE._serialized_end=2038
  _POSITIONSMESSAGE_GET_ALL_POSITIONS_PERFORMATIVE_PARAMSENTRY._serialized_start=1993
  _POSITIONSMESSAGE_GET_ALL_POSITIONS_PERFORMATIVE_PARAMSENTRY._serialized_end=2038
  _POSITIONSMESSAGE_GET_POSITION_PERFORMATIVE._serialized_start=2040
  _POSITIONSMESSAGE_GET_POSITION_PERFORMATIVE._serialized_end=2109
  _POSITIONSMESSAGE_ALL_POSITIONS_PERFORMATIVE._serialized_start=2112
  _POSITIONSMESSAGE_ALL_POSITIONS_PERFORMATIVE._serialized_end=2242
  _POSITIONSMESSAGE_POSITION_PERFORMATIVE._serialized_start=2244
  _POSITIONSMESSAGE_POSITION_PERFORMATIVE._serialized_end=2367
  _POSITIONSMESSAGE_ERROR_PERFORMATIVE._serialized_start=2370
  _POSITIONSMESSAGE_ERROR_PERFORMATIVE._serialized_end=2647
  _POSITIONSMESSAGE_ERROR_PERFORMATIVE_ERRORDATAENTRY._serialized_start=2599
  _POSITIONSMESSAGE_ERROR_PERFORMATIVE_ERRORDATAENTRY._serialized_end=2647
# @@protoc_insertion_point(module_scope)
