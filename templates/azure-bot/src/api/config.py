import os
from dotenv import load_dotenv

load_dotenv(override=True)


class Config:
    """Bot Configuration"""

    # DO NOT CHANGE THIS KEYS!!
    APP_ID = os.getenv("BOT_APP_ID")
    APP_PASSWORD = os.getenv("BOT_PASSWORD")
    APP_TENANTID = os.getenv("BOT_TENANT_ID")
    APP_TYPE = os.getenv("APP_TYPE", "singletenant")

    AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

    def validate(self):
        if not self.APP_ID or not self.APP_PASSWORD or not self.APP_TENANTID:
            raise Exception(
                "Missing required configuration. APP_ID, APP_PASSWORD, and APP_TENANT_ID must be set."
            )
        if not self.AZURE_OPENAI_MODEL or not self.AZURE_OPENAI_ENDPOINT:
            raise Exception(
                "Missing required configuration. AZURE_OPENAI_MODEL_DEPLOYMENT_NAME and AZURE_OPENAI_ENDPOINT must be set."
            )
        if not self.AZURE_OPENAI_API_VERSION:
            raise Exception(
                "Missing required configuration. AZURE_OPENAI_API_VERSION must be set."
            )


config = Config()
config.validate()
