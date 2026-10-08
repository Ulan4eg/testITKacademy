from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.wallets import router as wallets_router
from app.exceptions import WalletError

app = FastAPI(title="Wallet API")
app.include_router(wallets_router)


@app.exception_handler(WalletError)
async def wallet_error_handler(request: Request, exc: WalletError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
