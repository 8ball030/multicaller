# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: markets.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rmarkets.proto\x12\x1e\x61\x65\x61.eightballer.markets.v0_1_0\"\x9d\x0f\n\x0eMarketsMessage\x12^\n\x0b\x61ll_markets\x18\x05 \x01(\x0b\x32G.aea.eightballer.markets.v0_1_0.MarketsMessage.All_Markets_PerformativeH\x00\x12R\n\x05\x65rror\x18\x06 \x01(\x0b\x32\x41.aea.eightballer.markets.v0_1_0.MarketsMessage.Error_PerformativeH\x00\x12\x66\n\x0fget_all_markets\x18\x07 \x01(\x0b\x32K.aea.eightballer.markets.v0_1_0.MarketsMessage.Get_All_Markets_PerformativeH\x00\x12\\\n\nget_market\x18\x08 \x01(\x0b\x32\x46.aea.eightballer.markets.v0_1_0.MarketsMessage.Get_Market_PerformativeH\x00\x12T\n\x06market\x18\t \x01(\x0b\x32\x42.aea.eightballer.markets.v0_1_0.MarketsMessage.Market_PerformativeH\x00\x1a\xe8\x01\n\tErrorCode\x12Z\n\nerror_code\x18\x01 \x01(\x0e\x32\x46.aea.eightballer.markets.v0_1_0.MarketsMessage.ErrorCode.ErrorCodeEnum\"\x7f\n\rErrorCodeEnum\x12\x18\n\x14UNSUPPORTED_PROTOCOL\x10\x00\x12\x12\n\x0e\x44\x45\x43ODING_ERROR\x10\x01\x12\x13\n\x0fINVALID_MESSAGE\x10\x02\x12\x15\n\x11UNSUPPORTED_SKILL\x10\x03\x12\x14\n\x10INVALID_DIALOGUE\x10\x04\x1a\xf2\x03\n\x06Market\x1a\xe7\x03\n\x06Market\x12\n\n\x02id\x18\x01 \x01(\t\x12\x13\n\x0blowercaseId\x18\x02 \x01(\t\x12\x0e\n\x06symbol\x18\x03 \x01(\t\x12\x0c\n\x04\x62\x61se\x18\x04 \x01(\t\x12\r\n\x05quote\x18\x05 \x01(\t\x12\x0e\n\x06settle\x18\x06 \x01(\t\x12\x0e\n\x06\x62\x61seId\x18\x07 \x01(\t\x12\x0f\n\x07quoteId\x18\x08 \x01(\t\x12\x10\n\x08settleId\x18\t \x01(\t\x12\x0c\n\x04type\x18\n \x01(\t\x12\x0c\n\x04spot\x18\x0b \x01(\x08\x12\x0e\n\x06margin\x18\x0c \x01(\x08\x12\x0c\n\x04swap\x18\r \x01(\x08\x12\x0e\n\x06\x66uture\x18\x0e \x01(\x08\x12\x0e\n\x06option\x18\x0f \x01(\x08\x12\x0e\n\x06\x61\x63tive\x18\x10 \x01(\x08\x12\x10\n\x08\x63ontract\x18\x11 \x01(\x08\x12\x0e\n\x06linear\x18\x12 \x01(\x08\x12\x0f\n\x07inverse\x18\x13 \x01(\x08\x12\r\n\x05taker\x18\x14 \x01(\x02\x12\r\n\x05maker\x18\x15 \x01(\x02\x12\x14\n\x0c\x63ontractSize\x18\x16 \x01(\x02\x12\x0e\n\x06\x65xpiry\x18\x17 \x01(\x02\x12\x16\n\x0e\x65xpiryDatetime\x18\x18 \x01(\t\x12\x0e\n\x06strike\x18\x19 \x01(\x02\x12\x12\n\noptionType\x18\x1a \x01(\t\x12\x11\n\tprecision\x18\x1b \x01(\x02\x12\x0e\n\x06limits\x18\x1c \x01(\t\x12\x0c\n\x04info\x18\x1d \x01(\t\x1a\\\n\x07Markets\x1aQ\n\x07Markets\x12\x46\n\x07markets\x18\x01 \x03(\x0b\x32\x35.aea.eightballer.markets.v0_1_0.MarketsMessage.Market\x1a^\n\x1cGet_All_Markets_Performative\x12\x13\n\x0b\x65xchange_id\x18\x01 \x01(\t\x12\x10\n\x08\x63urrency\x18\x02 \x01(\t\x12\x17\n\x0f\x63urrency_is_set\x18\x03 \x01(\x08\x1a:\n\x17Get_Market_Performative\x12\n\n\x02id\x18\x01 \x01(\t\x12\x13\n\x0b\x65xchange_id\x18\x02 \x01(\t\x1a\x63\n\x18\x41ll_Markets_Performative\x12G\n\x07markets\x18\x01 \x01(\x0b\x32\x36.aea.eightballer.markets.v0_1_0.MarketsMessage.Markets\x1a\\\n\x13Market_Performative\x12\x45\n\x06market\x18\x01 \x01(\x0b\x32\x35.aea.eightballer.markets.v0_1_0.MarketsMessage.Market\x1a\x8d\x02\n\x12\x45rror_Performative\x12L\n\nerror_code\x18\x01 \x01(\x0b\x32\x38.aea.eightballer.markets.v0_1_0.MarketsMessage.ErrorCode\x12\x11\n\terror_msg\x18\x02 \x01(\t\x12\x64\n\nerror_data\x18\x03 \x03(\x0b\x32P.aea.eightballer.markets.v0_1_0.MarketsMessage.Error_Performative.ErrorDataEntry\x1a\x30\n\x0e\x45rrorDataEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\x0c:\x02\x38\x01\x42\x0e\n\x0cperformativeb\x06proto3')



_MARKETSMESSAGE = DESCRIPTOR.message_types_by_name['MarketsMessage']
_MARKETSMESSAGE_ERRORCODE = _MARKETSMESSAGE.nested_types_by_name['ErrorCode']
_MARKETSMESSAGE_MARKET = _MARKETSMESSAGE.nested_types_by_name['Market']
_MARKETSMESSAGE_MARKET_MARKET = _MARKETSMESSAGE_MARKET.nested_types_by_name['Market']
_MARKETSMESSAGE_MARKETS = _MARKETSMESSAGE.nested_types_by_name['Markets']
_MARKETSMESSAGE_MARKETS_MARKETS = _MARKETSMESSAGE_MARKETS.nested_types_by_name['Markets']
_MARKETSMESSAGE_GET_ALL_MARKETS_PERFORMATIVE = _MARKETSMESSAGE.nested_types_by_name['Get_All_Markets_Performative']
_MARKETSMESSAGE_GET_MARKET_PERFORMATIVE = _MARKETSMESSAGE.nested_types_by_name['Get_Market_Performative']
_MARKETSMESSAGE_ALL_MARKETS_PERFORMATIVE = _MARKETSMESSAGE.nested_types_by_name['All_Markets_Performative']
_MARKETSMESSAGE_MARKET_PERFORMATIVE = _MARKETSMESSAGE.nested_types_by_name['Market_Performative']
_MARKETSMESSAGE_ERROR_PERFORMATIVE = _MARKETSMESSAGE.nested_types_by_name['Error_Performative']
_MARKETSMESSAGE_ERROR_PERFORMATIVE_ERRORDATAENTRY = _MARKETSMESSAGE_ERROR_PERFORMATIVE.nested_types_by_name['ErrorDataEntry']
_MARKETSMESSAGE_ERRORCODE_ERRORCODEENUM = _MARKETSMESSAGE_ERRORCODE.enum_types_by_name['ErrorCodeEnum']
MarketsMessage = _reflection.GeneratedProtocolMessageType('MarketsMessage', (_message.Message,), {

  'ErrorCode' : _reflection.GeneratedProtocolMessageType('ErrorCode', (_message.Message,), {
    'DESCRIPTOR' : _MARKETSMESSAGE_ERRORCODE,
    '__module__' : 'markets_pb2'
    # @@protoc_insertion_point(class_scope:aea.eightballer.markets.v0_1_0.MarketsMessage.ErrorCode)
    })
  ,

  'Market' : _reflection.GeneratedProtocolMessageType('Market', (_message.Message,), {

    'Market' : _reflection.GeneratedProtocolMessageType('Market', (_message.Message,), {
      'DESCRIPTOR' : _MARKETSMESSAGE_MARKET_MARKET,
      '__module__' : 'markets_pb2'
      # @@protoc_insertion_point(class_scope:aea.eightballer.markets.v0_1_0.MarketsMessage.Market.Market)
      })
    ,
    'DESCRIPTOR' : _MARKETSMESSAGE_MARKET,
    '__module__' : 'markets_pb2'
    # @@protoc_insertion_point(class_scope:aea.eightballer.markets.v0_1_0.MarketsMessage.Market)
    })
  ,

  'Markets' : _reflection.GeneratedProtocolMessageType('Markets', (_message.Message,), {

    'Markets' : _reflection.GeneratedProtocolMessageType('Markets', (_message.Message,), {
      'DESCRIPTOR' : _MARKETSMESSAGE_MARKETS_MARKETS,
      '__module__' : 'markets_pb2'
      # @@protoc_insertion_point(class_scope:aea.eightballer.markets.v0_1_0.MarketsMessage.Markets.Markets)
      })
    ,
    'DESCRIPTOR' : _MARKETSMESSAGE_MARKETS,
    '__module__' : 'markets_pb2'
    # @@protoc_insertion_point(class_scope:aea.eightballer.markets.v0_1_0.MarketsMessage.Markets)
    })
  ,

  'Get_All_Markets_Performative' : _reflection.GeneratedProtocolMessageType('Get_All_Markets_Performative', (_message.Message,), {
    'DESCRIPTOR' : _MARKETSMESSAGE_GET_ALL_MARKETS_PERFORMATIVE,
    '__module__' : 'markets_pb2'
    # @@protoc_insertion_point(class_scope:aea.eightballer.markets.v0_1_0.MarketsMessage.Get_All_Markets_Performative)
    })
  ,

  'Get_Market_Performative' : _reflection.GeneratedProtocolMessageType('Get_Market_Performative', (_message.Message,), {
    'DESCRIPTOR' : _MARKETSMESSAGE_GET_MARKET_PERFORMATIVE,
    '__module__' : 'markets_pb2'
    # @@protoc_insertion_point(class_scope:aea.eightballer.markets.v0_1_0.MarketsMessage.Get_Market_Performative)
    })
  ,

  'All_Markets_Performative' : _reflection.GeneratedProtocolMessageType('All_Markets_Performative', (_message.Message,), {
    'DESCRIPTOR' : _MARKETSMESSAGE_ALL_MARKETS_PERFORMATIVE,
    '__module__' : 'markets_pb2'
    # @@protoc_insertion_point(class_scope:aea.eightballer.markets.v0_1_0.MarketsMessage.All_Markets_Performative)
    })
  ,

  'Market_Performative' : _reflection.GeneratedProtocolMessageType('Market_Performative', (_message.Message,), {
    'DESCRIPTOR' : _MARKETSMESSAGE_MARKET_PERFORMATIVE,
    '__module__' : 'markets_pb2'
    # @@protoc_insertion_point(class_scope:aea.eightballer.markets.v0_1_0.MarketsMessage.Market_Performative)
    })
  ,

  'Error_Performative' : _reflection.GeneratedProtocolMessageType('Error_Performative', (_message.Message,), {

    'ErrorDataEntry' : _reflection.GeneratedProtocolMessageType('ErrorDataEntry', (_message.Message,), {
      'DESCRIPTOR' : _MARKETSMESSAGE_ERROR_PERFORMATIVE_ERRORDATAENTRY,
      '__module__' : 'markets_pb2'
      # @@protoc_insertion_point(class_scope:aea.eightballer.markets.v0_1_0.MarketsMessage.Error_Performative.ErrorDataEntry)
      })
    ,
    'DESCRIPTOR' : _MARKETSMESSAGE_ERROR_PERFORMATIVE,
    '__module__' : 'markets_pb2'
    # @@protoc_insertion_point(class_scope:aea.eightballer.markets.v0_1_0.MarketsMessage.Error_Performative)
    })
  ,
  'DESCRIPTOR' : _MARKETSMESSAGE,
  '__module__' : 'markets_pb2'
  # @@protoc_insertion_point(class_scope:aea.eightballer.markets.v0_1_0.MarketsMessage)
  })
_sym_db.RegisterMessage(MarketsMessage)
_sym_db.RegisterMessage(MarketsMessage.ErrorCode)
_sym_db.RegisterMessage(MarketsMessage.Market)
_sym_db.RegisterMessage(MarketsMessage.Market.Market)
_sym_db.RegisterMessage(MarketsMessage.Markets)
_sym_db.RegisterMessage(MarketsMessage.Markets.Markets)
_sym_db.RegisterMessage(MarketsMessage.Get_All_Markets_Performative)
_sym_db.RegisterMessage(MarketsMessage.Get_Market_Performative)
_sym_db.RegisterMessage(MarketsMessage.All_Markets_Performative)
_sym_db.RegisterMessage(MarketsMessage.Market_Performative)
_sym_db.RegisterMessage(MarketsMessage.Error_Performative)
_sym_db.RegisterMessage(MarketsMessage.Error_Performative.ErrorDataEntry)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _MARKETSMESSAGE_ERROR_PERFORMATIVE_ERRORDATAENTRY._options = None
  _MARKETSMESSAGE_ERROR_PERFORMATIVE_ERRORDATAENTRY._serialized_options = b'8\001'
  _MARKETSMESSAGE._serialized_start=50
  _MARKETSMESSAGE._serialized_end=1999
  _MARKETSMESSAGE_ERRORCODE._serialized_start=533
  _MARKETSMESSAGE_ERRORCODE._serialized_end=765
  _MARKETSMESSAGE_ERRORCODE_ERRORCODEENUM._serialized_start=638
  _MARKETSMESSAGE_ERRORCODE_ERRORCODEENUM._serialized_end=765
  _MARKETSMESSAGE_MARKET._serialized_start=768
  _MARKETSMESSAGE_MARKET._serialized_end=1266
  _MARKETSMESSAGE_MARKET_MARKET._serialized_start=779
  _MARKETSMESSAGE_MARKET_MARKET._serialized_end=1266
  _MARKETSMESSAGE_MARKETS._serialized_start=1268
  _MARKETSMESSAGE_MARKETS._serialized_end=1360
  _MARKETSMESSAGE_MARKETS_MARKETS._serialized_start=1279
  _MARKETSMESSAGE_MARKETS_MARKETS._serialized_end=1360
  _MARKETSMESSAGE_GET_ALL_MARKETS_PERFORMATIVE._serialized_start=1362
  _MARKETSMESSAGE_GET_ALL_MARKETS_PERFORMATIVE._serialized_end=1456
  _MARKETSMESSAGE_GET_MARKET_PERFORMATIVE._serialized_start=1458
  _MARKETSMESSAGE_GET_MARKET_PERFORMATIVE._serialized_end=1516
  _MARKETSMESSAGE_ALL_MARKETS_PERFORMATIVE._serialized_start=1518
  _MARKETSMESSAGE_ALL_MARKETS_PERFORMATIVE._serialized_end=1617
  _MARKETSMESSAGE_MARKET_PERFORMATIVE._serialized_start=1619
  _MARKETSMESSAGE_MARKET_PERFORMATIVE._serialized_end=1711
  _MARKETSMESSAGE_ERROR_PERFORMATIVE._serialized_start=1714
  _MARKETSMESSAGE_ERROR_PERFORMATIVE._serialized_end=1983
  _MARKETSMESSAGE_ERROR_PERFORMATIVE_ERRORDATAENTRY._serialized_start=1935
  _MARKETSMESSAGE_ERROR_PERFORMATIVE_ERRORDATAENTRY._serialized_end=1983
# @@protoc_insertion_point(module_scope)
