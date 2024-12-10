from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.api.schemas.vv_response_schema import Product, PortCalls, Error
from app.api.schemas.schema_request import CarrierCode
from oracledb import AsyncConnection
from uuid import UUID
from typing import List, Dict, Optional, Any
from datetime import datetime


EVENT_TYPE: dict = {'UNL': 'Unloading', 'LOA': 'Loading', 'PAS': 'Pass'}


def construct_call(bound: str, voyage: List[str], port_event: Optional[str], port_name: Optional[str], port_code: Optional[str], event_time: datetime) -> Dict[str, Any]:
    return PortCalls.model_construct(
        bound=bound,
        voyage=voyage,
        portEvent=port_event,
        port={'portName': port_name, 'portCode': port_code},
        estimateDate=event_time.isoformat()).model_dump(warnings=False)


async def voyage_finder(connection: AsyncConnection, native_sql: str, placeholder: dict, product_id: UUID, scac: CarrierCode, voyage: str, vessel_imo: str):
    async with connection.cursor() as cursor:
        await cursor.execute(native_sql, placeholder)
        columns = [col[0] for col in cursor.description]
        cursor.rowfactory = lambda *args: dict(zip(columns, args))
        sql_result: list[dict] = await cursor.fetchall()
        if sql_result:
            grouped_data: dict = {key: [item for item in sql_result if (item['PORT_EVENT'], item['PORT_CODE'], item['EVENT_TIME']) == key] for key in {
                (item['PORT_EVENT'], item['PORT_CODE'], item['EVENT_TIME']) for item in sql_result}}
            duplicates: set = {key for key,
                               value in grouped_data.items() if len(value) > 1}
            unique_voyage_numbers: list = list(
                {entry['VOYAGE_NUM'] for entry in sql_result if entry['VOYAGE_NUM'] != voyage})
            unique_bounds: list = list(
                {bound['VOYAGE_DIRECTION'] for bound in sql_result}) if duplicates else ...
            port_of_calls: list = [
                construct_call(
                    bound=unique_bounds if (
                        port['PORT_EVENT'], port['PORT_CODE'], port['EVENT_TIME']) in duplicates else port.get('VOYAGE_DIRECTION'),
                    voyage=[voyage, unique_voyage_numbers[0]] if (
                        port['PORT_EVENT'], port['PORT_CODE'], port['EVENT_TIME']) in duplicates else port.get('VOYAGE_NUM'),
                    port_event=EVENT_TYPE.get(port.get('PORT_EVENT')),
                    port_name=port.get('PORT_NAME'),
                    port_code=port.get('PORT_CODE'),
                    event_time=port['EVENT_TIME']
                )
                for port in sql_result
            ]
            remove_dup: list[dict] = [org_data for seq, org_data in enumerate(
                port_of_calls) if org_data not in port_of_calls[seq + 1:]] if duplicates else ...
            api_result = Product(productid=product_id, scac=scac, voyage=voyage, nextVoyage=unique_voyage_numbers[0] if unique_voyage_numbers else None,
                                 vessel={'vesselName': sql_result[0].get(
                                     'VESSEL_NAME'), 'imo': sql_result[0].get('VESSEL_IMO')},
                                 services={'serviceCode': sql_result[0].get(
                                     'SERVICE_CODE')},
                                 calls=[org_data | {'seq': seq+1} for seq, org_data in enumerate(remove_dup)] if duplicates else port_of_calls).model_dump(mode='json', exclude_none=True)

        else:
            api_result = JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=jsonable_encoder(Error(
                id=product_id, detail=f"No any vessel voyage found for scac:{scac},imo:{vessel_imo} and voyage:{voyage} ")))
        return api_result
