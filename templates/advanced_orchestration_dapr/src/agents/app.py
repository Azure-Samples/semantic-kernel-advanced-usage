import tracing
import logging
from dapr.ext.fastapi import DaprActor
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sk_actor import SKAgentActor
from dotenv import load_dotenv

load_dotenv(override=True, verbose=True)


# Configure logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN)
logging.getLogger("sk_ext").setLevel(logging.DEBUG)


tracing.set_up_logging()
tracing.set_up_tracing()
tracing.set_up_metrics()


# Suppress health probe logs from the Uvicorn access logger
# Dapr runtime calls it frequently and pollutes the logs
class HealthProbeFilter(logging.Filter):
    def filter(self, record):
        # Suppress log messages containing the health probe request
        return (
            "/health" not in record.getMessage()
            and "/healthz" not in record.getMessage()
        )


# Add the filter to the Uvicorn access logger
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.addFilter(HealthProbeFilter())

actor: DaprActor = None

# Register actor when fastapi starts up


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Registering actor")
    await actor.register_actor(SKAgentActor)
    yield


# Create fastapi and register dapr and actors
app = FastAPI(title="SK Agent Dapr Actors host", lifespan=lifespan)
actor = DaprActor(app)
