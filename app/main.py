from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from app.api.handler.pfa_schedule import poc_schedule
from app.api.handler.vessel_voyage import voyage_router
from app.storage import oracle_db_pool
from app.internal.setting import log_queue_listener
import uvicorn
import atexit


# 👇 Initalize the Oracle ConnectionPool before starting the application
@asynccontextmanager
async def lifespan(app: FastAPI):
    queue_lister.start()
    await oracle_db_pool.create_pool()
    yield
    atexit.register(queue_lister.stop)
    await oracle_db_pool.close_pool()

#
queue_lister = log_queue_listener()
app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(GZipMiddleware, minimum_size=4000)
app.add_middleware(CORSMiddleware, allow_origins=[
                   "*"], allow_credentials=True, allow_methods=['GET'], allow_headers=["*"])
app.include_router(voyage_router.router)
app.include_router(poc_schedule.router)


@app.get("/docs", include_in_schema=False)
def overridden_swagger():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Vessel Voyage API",
                               swagger_favicon_url="https://ca.kuehne-nagel.com/o/kn-lgo-theme/images/favicons/favicon.ico")


@app.get("/redoc", include_in_schema=False)
def overridden_redoc():
    return get_redoc_html(openapi_url="/openapi.json", title="Vessel Voyage API",
                          redoc_favicon_url="https://ca.kuehne-nagel.com/o/kn-lgo-theme/images/favicons/favicon.ico")


def custom_openapi():
    """
    By using this way,this application won't have to generate the schema every time a user opens our API docs.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="API Vessel Voyage",
        version="1.0.1",
        description="Get Single Source Of Truth In Real Time",
        contact={'pic': 'neck.chi@kuehne-nagel.com'},
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://ca.kuehne-nagel.com/o/kn-lgo-theme/images/kuehne-nagel-logo-blue.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080,
                timeout_keep_alive=60, reload=True)
