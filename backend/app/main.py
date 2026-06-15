from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.bootstrap import ensure_schema
from app.db.base import Base
from app.db.session import engine
from app.routers.inventory import router as inventory_router
from app.routers.monthly_inventory import router as monthly_inventory_router
from app.routers.products import router as products_router
from app.routers.reports import router as reports_router
from app.routers.stock_movements import router as stock_movements_router


app = FastAPI(title="Inventory Management API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(products_router)
app.include_router(inventory_router)
app.include_router(stock_movements_router)
app.include_router(reports_router)
app.include_router(monthly_inventory_router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_schema(engine)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
