import logging
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
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


@app.get("/")
async def root():
    """
    Root endpoint for the bot service.
    """
    return JSONResponse(content={"message": "Hello from Azure Bot Service!"})


@app.get("/manifest/copilot-studio", response_class=JSONResponse)
async def manifest():
    # load manifest from file and interpolate with env vars
    with open("copilot-studio.manifest.json") as f:

        manifest = f.read()

        # Get container app current ingress fqdn
        # See https://learn.microsoft.com/en-us/azure/container-apps/environment-variables?tabs=portal
        fqdn = f"https://{os.getenv('CONTAINER_APP_NAME')}.{os.getenv('CONTAINER_APP_ENV_DNS_SUFFIX')}/api/messages"

        manifest = manifest.replace("__botEndpoint", fqdn).replace(
            "__botAppId", config.APP_ID
        )

    return JSONResponse(content=json.loads(manifest))



# GET /manifest/teams to return the manifest for Teams in a zip file
@app.get("/manifest/teams")
async def manifest_teams():
    import os
    import zipfile
    import io

    # determine the base directory of the current file
    base_dir = os.path.dirname(__file__)

    # load manifest from file and interpolate with env vars using an absolute path
    manifest_path = os.path.join(base_dir, "teams_package", "manifest.json")
    with open(manifest_path, "r") as f:
        manifest = f.read()

    manifest = (
        manifest.replace("__botAppId", config.APP_ID)
        .replace("__teamsAppId", config.TEAMS_APP_ID)
        .replace("__teamsAppName", config.TEAMS_APP_NAME)
    )

    # Create a zip file with the manifest and the icon using absolute paths for the icons
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        # Add the manifest file
        zip_file.writestr("manifest.json", manifest)

        # Add the icon files
        icon_files = [
            ("outline.png", os.path.join(base_dir, "teams_package", "outline.png")),
            ("color.png", os.path.join(base_dir, "teams_package", "color.png")),
        ]
        for arcname, file_path in icon_files:
            with open(file_path, "rb") as icon:
                zip_file.writestr(arcname, icon.read())
    # Move the buffer position to the beginning
    zip_buffer.seek(0)
    # Create a response with the zip file
    response = StreamingResponse(zip_buffer, media_type="application/zip")
    # Set the filename for the download
    response.headers["Content-Disposition"] = (
        f"attachment; filename={config.TEAMS_APP_NAME}.zip"
    )
    # Return the response
    return response
