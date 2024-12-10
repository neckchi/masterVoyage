from enum import StrEnum
from typing import Literal, Annotated, Optional
from pydantic import BaseModel, Field


class PortEvent(StrEnum):
    loading = "Loading"
    unloading = "Unloading"
    transfer = 'Transfer'
    omit = "Omit"
    pas = 'Pass'


CarrierCode = Literal['MSCU', 'CMDU', 'ANNU', 'APLU', 'CHNL', 'CSFU', 'ONEY', 'HDMU', 'ZIMU',
                      'MAEU', 'MAEI', 'OOLU', 'COSU', 'HLCU', 'YMJA', 'YMLU', 'YMPR', 'EGLV', 'SMLM', 'WHLC', 'IAAU']


class QueryParams(BaseModel):
    model_config = {"extra": "forbid"}
    scac:  CarrierCode
    vessel_imo: Annotated[str, Field(
        validation_alias='vesselIMO', serialization_alias='vesselIMO', max_length=7)]
    voyage: Annotated[str, Field(
        validation_alias='voyage', serialization_alias='voyage', max_length=15)]
