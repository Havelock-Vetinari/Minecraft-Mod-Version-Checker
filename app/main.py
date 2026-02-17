from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import asyncio

from app.core.database import Base, engine
from app.routers import versions, mods, results
from app.services.background import background_loop

# Create tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background job
    bg_task = asyncio.create_task(background_loop())
    yield
    # Shutdown: No specific cleanup for background loop needed as it's daemon-like, 
    # but could cancel if we kept a reference.
    bg_task.cancel()
    try:
        await bg_task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="Minecraft Mod Compatibility Checker", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles

# Include routers
app.include_router(versions.router)
app.include_router(mods.router)
app.include_router(results.router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    """Serve index.html"""
    return FileResponse("index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
