import oracledb
import logging
import asyncio
from app.internal.setting import Settings
from uuid import uuid4
from typing import Optional
from oracledb import AsyncConnectionPool


class OracleDBConnectionPool:
    credential = Settings()
    def __init__(self, user=credential.db_user.get_secret_value(), password=credential.db_pw.get_secret_value(),
                 dsn = oracledb.makedsn(host=credential.host.get_secret_value(),port = credential.port, service_name=credential.service_name.get_secret_value()), concurrency=20,max_retries=5):
        self.user:str = user
        self.password:str = password
        self.dsn:str = dsn
        self.concurrency:int = concurrency
        self.pool:Optional[AsyncConnectionPool] = None
        self.max_retries = max_retries

    async def create_pool(self):
        retries: int = 0
        while retries < self.max_retries:
            try:
                self.pool =  oracledb.create_pool_async(user=self.user, password=self.password, dsn=self.dsn,min=self.concurrency, max=self.concurrency,retry_count = 5)
                logging.info(f"Successfully created SeaSchedule Oracle DB pool")
                return self.pool
            except oracledb.Error as e:
                logging.error(f"Error creating Oracle DB pool: {e}")
                retries += 1
                await asyncio.sleep(1)
        logging.error(f"DB connection pool creation reached maximum retries.")

    async def get_connection(self):
        retries: int = 0
        while retries < self.max_retries:
            try:
                session_id: str = str(uuid4())
                async with self.pool.acquire() as conn:
                    logging.info(f'Acquire connection from DB pool - {session_id}')
                    yield conn
                    logging.info(f'Release connection back to DB pool - {session_id}')
                    await self.pool.release(conn)
                    break
            except oracledb.Error as error_pool:
                logging.error(f"Error creating connection from  DB pool: {error_pool}")
                retries += 1
                await asyncio.sleep(1)

    async def close_pool(self):
        await self.pool.close(force=True)




