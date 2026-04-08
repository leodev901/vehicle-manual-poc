from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.api.endpoint.health import api_router as health_router





def register_reoutes(app:FastAPI):

    app.include_router(health_router)

    @app.get("/")
    async def root():
        return RedirectResponse(url="/docs")



    
    

    