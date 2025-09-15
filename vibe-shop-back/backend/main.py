from fastapi import FastAPI
from utils import ensure_images_synced, mount_images
from fastapi.middleware.cors import CORSMiddleware

from db import init_sqlite, ensure_admin_user
from routes import products as products_router
from routes import checkout as checkout_router
from routes import reviews as reviews_router
from routes import admin as admin_router
from routes import auth as auth_router


app = FastAPI()

# Static/images
ensure_images_synced()
mount_images(app)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB initialization
init_sqlite()
ensure_admin_user()

# Routers
app.include_router(products_router.router)
app.include_router(checkout_router.router)
app.include_router(reviews_router.router)
app.include_router(admin_router.router)
app.include_router(auth_router.router)


@app.get("/")
async def root():
    return {"status": "ok"}

