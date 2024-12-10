from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from .schema_request import CarrierCode, PortEvent
from datetime import datetime


class PortBase(BaseModel):
    model_config = ConfigDict(cache_strings='all')
    portName: str | None = Field(max_length=100, default=None)
    portCode: str = Field(
        max_length=5, title="Port Of Discharge", pattern=r"[A-Z]{2}[A-Z0-9]{3}")
    terminalName: str | None = Field(max_length=100, default=None)
    terminalCode: str | None = Field(default=None, max_length=20)


class VesselDetails(BaseModel):
    model_config = ConfigDict(cache_strings='all')
    vesselName: str | None = Field(
        title='Vessel Name', description='VesselName', max_length=100)
    imo: int | str | None = Field(
        max_length=7, title='Vessel IMO Code', description='Vessel IMO Code', pattern=r"[0-9]{7}")


class Service(BaseModel):
    model_config = ConfigDict(cache_strings='all')
    serviceCode: str | None = Field(default=None, max_length=100)
    serviceName: str | None = Field(default=None, max_length=100)


class PortCalls(BaseModel):
    model_config = ConfigDict(cache_strings='all')
    seq: int | None = Field(
        ge=1, description='Sequence of Port Calls', default=None)
    bound: list[str] | str | None = Field(
        description='Direction Code', default=None)
    voyage: list[str] | str = Field(max_length=20)
    portEvent: PortEvent
    port: PortBase = Field(description="This could be point/port")
    estimateDate: datetime | None = Field(
        description="eventDate will be ignored for omitted port", default=None)
    actualDate: datetime | None = Field(
        description="eventDate will be ignored for omitted port", default=None)


class Product(BaseModel):
    productid: UUID = Field(
        description='Generate UUID based on the request params')
    scac: CarrierCode = Field(max_length=4, title="Carrier Code",
                              description="This is SCAC.It must be 4 characters",)
    vessel: VesselDetails = Field(
        title='Vessel Details', description='Vessel Name and IMO Code')
    voyage: str = Field(max_length=20)
    previousVoyage: str | None = Field(default=None, max_length=20)
    nextVoyage: str | None = Field(default=None, max_length=20)
    services: Service | None = Field(default=None, title="Service Loop")
    calls: list[PortCalls] | None = Field(
        default=None, title='Number Of Port Call', description="The number of ports to be called")


class Error(BaseModel):
    id: UUID
    detail: str
