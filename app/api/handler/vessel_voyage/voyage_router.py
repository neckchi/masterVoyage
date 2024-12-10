from fastapi import APIRouter, Query, Depends, Request
from app.api.schemas.schema_request import QueryParams
from app.api.schemas.vv_response_schema import Product
from app.api.handler.vessel_voyage.voyage_handler import voyage_finder
from app.internal.setting import Settings, get_settings
from app.storage import oracle_db_pool
from app.internal.security import basic_auth
from typing import Annotated
from uuid import uuid5, NAMESPACE_DNS
from pathlib import Path
import logging

router = APIRouter(prefix='/voyage', tags=["API Vessel Voyage"])


@router.get("/route", summary="Search Point To Point schedules from carriers", response_model=Product,
            response_model_exclude_defaults=True,
            response_description='Return all port of calls for vessel voyage')
async def get_voyage(request: Request,
                     query_params: Annotated[QueryParams, Query()],
                     credentials=Depends(basic_auth),
                     settings: Settings = Depends(get_settings),
                     conn=Depends(oracle_db_pool.get_connection)):
    file_path = settings.sql_file_path.get_secret_value()
    native_sql = Path(file_path).read_text()
    logging.info(
        f'Received a request with following parameters:{request.url.query}')
    placeholder: dict = {"scac": query_params.scac,
                         "voyage": query_params.voyage, "imo": query_params.vessel_imo}
    return await voyage_finder(connection=conn, native_sql=native_sql, placeholder=placeholder, product_id=uuid5(NAMESPACE_DNS, str(request.url)), scac=query_params.scac, voyage=query_params.voyage, vessel_imo=query_params.vessel_imo)
