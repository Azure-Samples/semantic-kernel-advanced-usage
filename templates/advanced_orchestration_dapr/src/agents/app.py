from dotenv import load_dotenv

load_dotenv(override=True, verbose=True)

from sk_actor import SKAgentActor
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dapr.ext.fastapi import DaprActor


# Configure logging
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN)
logging.getLogger("sk_ext").setLevel(logging.DEBUG)

import tracing

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

# import debugpy

# # Start the debug server on port 5678
# debugpy.listen(("localhost", 5678))


# Register actor when fastapi starts up
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Registering actor")
    await actor.register_actor(SKAgentActor)
    yield


# Create fastapi and register dapr and actors
app = FastAPI(title="SK Agent Dapr Actors host", lifespan=lifespan)
actor = DaprActor(app)

# Future, for async communication over pubsub
# PUBSUB_NAME = os.getenv("PUBSUB_NAME", "workflow")
# TOPIC_NAME = os.getenv("TOPIC_NAME", "events")
# dapr_app = DaprApp(app)
# @dapr_app.subscribe(
#     pubsub=PUBSUB_NAME,
#     topic=TOPIC_NAME,
# )
# async def handle_workflow_input(req: Request):
#     try:

#         # Read fastapi request body as text
#         body = await req.body()
#         logger.info(f"Received workflow input: {body}")

#         # Parse the body as a CloudEvent
#         event = from_http(data=body, headers=req.headers)

#         data = InputWorkflowEvent.model_validate(event.data)
#         proxy: WorkflowActorInterface = ActorProxy.create(
#             "WorkflowActor", ActorId(data.id), WorkflowActorInterface
#         )
#         await proxy.run(data.input)

#         return {"status": "SUCCESS"}
#     except Exception as e:
#         logger.error(f"Error handling workflow input: {e}")
#         return {"status": "DROP", "message": str(e)}
