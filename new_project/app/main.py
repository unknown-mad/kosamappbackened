import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from .database import engine, Base
from . import model  # noqa: F401 - register models with Base
from .routers import (
    account,
    address,
    approval,
    auth,
    bureau_score,
    contact_us,
    debug_journey,
    employment,
    lender_assignment,
    lenders,
    permission,
    profile,
    reference,
    selfie,
    user,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def _add_journey_columns(conn) -> None:
    """Add new journey columns if missing (create_all does not alter existing tables)."""
    cols = [
        "banking_completed",  # ensure it exists (legacy tables may lack it)
        "loan_offer_completed", "loan_detail_completed", "kyc_completed",
        "selfie_completed", "address_completed", "reference_completed",
        "account_completed", "employment_completed", "emandate_completed", "e_sign_completed",
    ]
    for c in cols:
        conn.execute(text(
            f"ALTER TABLE kosam_uat.user_journey_status ADD COLUMN IF NOT EXISTS {c} INTEGER DEFAULT 0"
        ))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create schema and table on startup."""
    logger.info("Creating schema kosam_uat and table contacts...")
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS kosam_uat"))
            await conn.run_sync(Base.metadata.create_all)
            await conn.run_sync(_add_journey_columns)
        logger.info("SUCCESS: Schema kosam_uat and table contacts created. Data saves to: postgres.kosam_uat.contacts")
    except Exception as e:
        logger.error("FAILED to create table: %s", e)
        traceback.print_exc()
        raise
    yield


app = FastAPI(title="KosamApp API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
    )


app.include_router(auth.router, prefix="/api")
app.include_router(profile.router, prefix="/api/profile")
app.include_router(permission.router, prefix="/api/permissions")
app.include_router(bureau_score.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(contact_us.router, prefix="/api")
app.include_router(lender_assignment.router, prefix="/api")
app.include_router(debug_journey.router, prefix="/api")
app.include_router(lenders.router, prefix="/api")
app.include_router(address.router, prefix="/api")
app.include_router(reference.router, prefix="/api")
app.include_router(employment.router, prefix="/api")
app.include_router(selfie.router, prefix="/api")
app.include_router(account.router, prefix="/api")
app.include_router(approval.router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "Hello from KosamApp Backend!"}


@app.get("/status")
def status():
    return {"status": "ok", "database": "postgres", "schema": "kosam_uat", "table": "contacts"}


@app.get("/schema/kosam_uat")
async def show_schema_data():
    """Show tables and row counts in kosam_uat schema."""
    async with engine.connect() as conn:
        tables_result = await conn.execute(
            text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'kosam_uat'
                ORDER BY table_name
            """)
        )
        tables = [row[0] for row in tables_result.fetchall()]

        data = {"schema": "kosam_uat", "database": "postgres", "tables": {}}
        for table in tables:
            count_result = await conn.execute(
                text("SELECT COUNT(*) FROM kosam_uat.{}".format(table))
            )
            count = count_result.scalar()
            if isinstance(count, tuple):
                count = count[0]
            rows_result = await conn.execute(
                text("SELECT * FROM kosam_uat.{}".format(table))
            )
            rows = [dict(row._mapping) for row in rows_result.fetchall()]
            data["tables"][table] = {"count": count, "rows": rows}
        await conn.commit()
    return data
