# app/routers/status.py

from fastapi import APIRouter, Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from app.kernel.aols import get_genesis_state

router = APIRouter()

API_KEY_HEADER = APIKeyHeader(name="X-Dispatcher-API-Key", auto_error=False)

AUTHORIZED_KEYS = {
    "akhilesh-decisionassure-node": "PARTNER_READ",
    "eric-scqos-gateway": "PARTNER_READ",
}

async def verify_partner_key(api_key: str = Security(API_KEY_HEADER)):
    if not api_key or api_key not in AUTHORIZED_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AUTHORITY_FAILURE: Invalid or missing API key."
        )
    return AUTHORIZED_KEYS[api_key]

@router.get("/status")
async def get_system_status(clearance: str = Security(verify_partner_key)):
    state = get_genesis_state()
    return {
        "system":      "Dispatcher AO",
        "version":     "1.0.0",
        "genesis_cid": state["genesis_cid"],
        "sequence":    state["current_sequence"],
        "status":      state["integration_status"],
        "clearance":   clearance,
        "timestamp":   state["last_updated"]
    }