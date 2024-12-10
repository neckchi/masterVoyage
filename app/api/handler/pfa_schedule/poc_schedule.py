from fastapi import APIRouter, Query, status, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.api.schemas import poc_schedule_schema, schema_request
from app.storage import oracle_db_pool
from app.internal.security import basic_auth
from app.internal.setting import Settings, get_settings
from uuid import uuid5, NAMESPACE_DNS, UUID
from pathlib import Path
from datetime import datetime, timedelta, date

router = APIRouter(prefix='/schedules', tags=["POC Schedule"])
# The degree of parallelism / number of connections to open
NUM_THREADS = 10
# How many rows to fetch in each thread
BATCH_SIZE = 50
# Internal buffer size: Tune this for performance
ARRAY_SIZE = 100


@router.get("/poc", summary="Proof Of Concept - P2P Schedule", response_model=poc_schedule_schema.Product,
            response_model_exclude_defaults=True,
            response_description='Return p2p schedule')
async def get_voyage(point_from: str = Query(alias='pointFrom', default=..., max_length=5, regex=r"[A-Z]{2}[A-Z0-9]{3}", example='HKHKG', description='Search by either port or point of origin'),
                     point_to: str = Query(alias='pointTo', default=..., max_length=5,
                                           regex=r"[A-Z]{2}[A-Z0-9]{3}", example='DEHAM', description="Search by either port or point of destination"),
                     etd_start: date = Query(alias='etdStartDate', default=..., example=datetime.now(
                     ).strftime("%Y-%m-%d"), description='YYYY-MM-DD'),
                     etd_end: date | None = Query(alias='etdEndDate', default=None, example=datetime.now(
                     ) + timedelta(weeks=4), description='YYYY-MM-DD'),
                     scac: list[schema_request.CarrierCode | None] = Query(
                         default=[None], description='Prefer to search p2p schedule by scac.Empty means searching for all API schedules'),
                     service_code: str | None = Query(
                         alias='serviceCode', default=None, description='Search by either service code or service name', max_length=30),
                     page: int = Query(
                         alias='offset', default=0, description='the offset for pagination start from 0 by default. each page contains 30 result'),
                     credentials=Depends(basic_auth),
                     settings: Settings = Depends(get_settings),
                     conn=Depends(oracle_db_pool.get_connection)):
    file_path = settings.poc_file_path.get_secret_value()
    native_sql = Path(file_path).read_text()
    product_id: UUID = uuid5(
        NAMESPACE_DNS, f'{scac}-p2p-api-{point_from}{point_to}{etd_start}{etd_end}{service_code}{page}')
    placeholder: dict = {"row_offset": (page*BATCH_SIZE), "max_rows": BATCH_SIZE, "pol": point_from, "pod": point_to,
                         "etd_start": etd_start.strftime('%Y-%m-%d'), "etd_end": (etd_start + timedelta(weeks=4)).strftime('%Y-%m-%d')}
    async with conn.cursor() as cursor:
        cursor.prefetchrows = 2
        cursor.arraysize = ARRAY_SIZE
        await cursor.execute(native_sql, placeholder)
        columns = [col[0] for col in cursor.description]
        cursor.rowfactory = lambda *args: dict(zip(columns, args))
        sql_result: list[dict] = await cursor.fetchmany()
    if sql_result:
        poc_schedule = [
            poc_schedule_schema.Schedule.model_construct(scac=leg.get('SCAC'), pointFrom=(pol := leg['POL_PORT_CODE']),
                                                         pointTo=(pod := leg.get('POD_PORT_CODE') if leg.get(
                                                             'POD_PORT_CODE') else leg.get('SUB_POD_PORT_CODE')),
                                                         etd=(etd := leg['POL_EVENT_TIME']), eta=(eta := leg['POD_EVENT_TIME'] if leg.get('POD_EVENT_TIME') else leg.get('SUB_POD_EVENT_TIME')), transitTime=(tt := int((eta - etd).days)),
                                                         transshipment='False', legs=[
                poc_schedule_schema.Leg.model_construct(pointFrom={'locationCode': pol}, pointTo={'locationCode': pod}, etd=etd, eta=eta, transitTime=tt,
                                                        transportations={'transportType': 'Vessel', 'transportName': leg.get(
                                                            'VESSEL_NAME'), 'referenceType': 'IMO', 'reference':  leg.get('VESSEL_IMO')},
                                                        services={'serviceCode': leg.get('SERVICE_CODE')} if leg.get(
                    'SERVICE_CODE') else None,
                    voyages={'internalVoyage': leg.get('VOYAGE_NUM'), 'subSequentVoyage': leg.get('SUB_VOYAGE_NUM')}).model_dump(warnings=False)]).model_dump(warnings=False) for leg in sql_result]
        sorted_schedules: list = sorted(
            poc_schedule, key=lambda tt: (tt['etd'], tt['transitTime']))
        api_result = poc_schedule_schema.Product(
            productid=product_id,
            origin=point_from,
            destination=point_to, noofSchedule=len(sorted_schedules),
            schedules=sorted_schedules).model_dump(mode='json', exclude_none=True)
        return api_result
    else:
        api_result = JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=jsonable_encoder(
            poc_schedule_schema.Error(id=product_id, detail=f"No poc schedule found ")))
    return api_result
