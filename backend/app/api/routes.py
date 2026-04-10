from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.api.endpoints.health import api_router as health_router
from app.api.endpoints.chat import api_router as chat_router
from app.api.endpoints.manual import api_router as manual_router




def register_routes(app:FastAPI):

    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(manual_router)

    @app.get("/")
    async def root():
        return RedirectResponse(url="/docs")



    
    

    