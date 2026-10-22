"""Inicialização: python -m whatsapp_mcp"""
from .server import settings

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "whatsapp_mcp.server:app",
        host=settings.bind_host,
        port=settings.port,
        workers=1,
        proxy_headers=False,
    )
