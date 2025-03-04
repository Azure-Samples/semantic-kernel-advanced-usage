import logging
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
import json
import os
from teamsBot import bot
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.post("/api/messages", response_class=Response)
async def on_messages(req: Request) -> Response:
    """
    Endpoint for processing messages with the Teams Bot.
    """
    logger.info("Received a message.")

    content_type = req.headers.get("Content-Type", "").lower()
    if "application/json" in content_type:
        try:
            body = await req.json()
            logger.info("Request body: %s", body)
        except Exception as e:
            logger.error("Error parsing JSON payload: %s", e)
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Process the incoming request
    # This will send a reply activity to the user,
    # so we don't need to return anything here
    await bot.process(req)

    return Response(status_code=200)


@app.get("/manifest", response_class=JSONResponse)
async def manifest():
    # load manifest from file and interpolate with env vars
    with open("manifest.json") as f:
        manifest = f.read()

        # Get container app current ingress fqdn
        # See https://learn.microsoft.com/en-us/azure/container-apps/environment-variables?tabs=portal
        fqdn = f"https://{os.getenv('CONTAINER_APP_NAME')}.{os.getenv('CONTAINER_APP_ENV_DNS_SUFFIX')}/api/messages"

        manifest = manifest.replace("__botEndpoint", fqdn).replace(
            "__botAppId", config.APP_ID
        )

    return JSONResponse(content=json.loads(manifest))
