import logging

from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.post("/web-vitals")
async def receive_web_vitals(request: Request):
    """Receive Web Vitals metrics from the frontend."""
    try:
        metric = await request.json()
        logger.info(f"Web Vitals: {metric}")
        return {"status": "success", "message": "Web Vitals received"}
    except Exception as e:
        logger.error(f"Error receiving Web Vitals: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Error receiving Web Vitals: {e!s}"
        )
