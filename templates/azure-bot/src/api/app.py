import logging
from aiohttp import web
from aiohttp.web import Request
import json
import os
from bot import bot
from config import config

from dotenv import load_dotenv

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Primary endpoint for processing messages,
# both with Teams and Copilot Studio
async def messages(req: Request):
    """
    Endpoint for processing messages with the Teams Bot.
    """
    logger.info("Received a message.")
    body = await req.json()
    logger.info("Request body: %s", body)

    # Process the incoming request
    return await bot.process(req)


async def copilot_manifest(req: Request):
    # load manifest from file and interpolate with env vars
    with open("copilot-studio.manifest.json") as f:

        manifest = f.read()

        # Get container app current ingress fqdn
        # See https://learn.microsoft.com/en-us/azure/container-apps/environment-variables?tabs=portal
        # fqdn = f"https://{os.getenv('CONTAINER_APP_NAME')}.{os.getenv('CONTAINER_APP_ENV_DNS_SUFFIX')}/api/messages"
        fqdn = os.getenv("ENDPOINT_URL")

        manifest = manifest.replace("__botEndpoint", fqdn).replace(
            "__botAppId", config.APP_ID
        )

    return json.loads(manifest)


# GET /manifest/teams to return the manifest for Teams in a zip file
async def manifest_teams(req: Request):
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
    response = web.StreamResponse(
        status=200,
        headers={
            "Content-Type": "application/zip",
            "Content-Disposition": f"attachment; filename={config.TEAMS_APP_NAME}.zip",
        },
    )
    await response.prepare(req)
    await response.write(zip_buffer.read())
    await response.write_eof()

    # Return the response
    return response


APP = web.Application()
APP.router.add_post("/api/messages", messages)
APP.router.add_get("/manifest/teams", manifest_teams)
APP.router.add_get("/manifest/copilot", copilot_manifest)

if __name__ == "__main__":
    try:
        web.run_app(APP, host="0.0.0.0", port=5001)
    except Exception as error:
        raise error
