from enum import StrEnum
from typing import Literal, Annotated, Optional
from pydantic import BaseModel, Field


class PortEvent(StrEnum):
    loading = "Loading"
    unloading = "Unloading"
    transfer = 'Transfer'
    omit = "Omit"
    pas = 'Pass'


class CarrierCode(StrEnum):
    MSCU = 'MSCU'
    CMDU = 'CMDU'
    ANNU = 'ANNU'
    APLU = 'APLU'
    CHNL = 'CHNL'
    CSFU = 'CSFU'
    ONEY = 'ONEY'
    HDMU = 'HDMU'
    ZIMU = 'ZIMU'
    MAEU = 'MAEU'
    MAEI = 'MAEI'
    OOLU = 'OOLU'
    COSU = 'COSU'
    HLCU = 'HLCU'
    YMJA = 'YMJA'
    YMLU = 'YMLU'
    YMPR = 'YMPR'
    EGLV = 'EGLV'
    SMLM = 'SMLM'
    WHLC = 'WHLC'
    IAAU = 'IAAU'



class QueryParams(BaseModel):
    model_config = {"extra": "forbid"}
    scac:  CarrierCode
    vessel_imo: Annotated[str, Field(
        validation_alias='vesselIMO', serialization_alias='vesselIMO', max_length=7)]
    voyage: Annotated[str, Field(
        validation_alias='voyage', serialization_alias='voyage', max_length=15)]
