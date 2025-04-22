from typing import Annotated
import json
from sk_ext.basic_kernel import create_service
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.functions import kernel_function


class SalesAgentPlugin:
    def __init__(self):
        # Offers data with internal fields (starting with '_') that should not be shared with the customer.
        self.offers = {
            "All voice plan": {
                "Description": "All voice plan for unlimited calls.",
                "Price": "€10/month",
                "Details": "Unlimited calls to all networks, 50GB data included, extra data €1/GB.",
                "_SKU": "VOICE_ALL",
            },
            "Mobile Internet": {
                "Description": "Mobile WiFi for you to take anywhere, supports up to 10 devices.",
                "Price": "€10/month",
                "Details": "100GB data included, €1/GB after that. 120 minutes of calls and 100 SMS.",
                "_SKU": "INET_MOBILE",
            },
            "Large Data Plan": {
                "Description": "High data plan for heavy users.",
                "Price": "€20/month",
                "Details": "250GB data included, €0.50/GB after that. Unlimited calls and SMS.",
                "_SKU": "INET_LARGE",
            },
            "Extra Large Data Plan": {
                "Description": "Unlimited data plan for power users.",
                "Price": "€50/month",
                "Details": "Unlimited data at 5G speeds. Unlimited calls and SMS.",
                "_SKU": "INET_XLARGE",
            },
            "All-in-One Bundle": {
                "Description": "Mobile internet and home internet in one package.",
                "Price": "€45/month",
                "Details": "100GB mobile data, €1/GB after that. Home internet included.",
                "_SKU": "INET_BUNDLE",
            },
            "Home Internet": {
                "Description": "High-speed internet for your home.",
                "Price": "€30/month",
                "Details": "Unlimited home data at 1Gbps.",
                "_SKU": "INET_HOME",
            },
        }

    @kernel_function
    def get_offers(
        self,
    ) -> Annotated[str, "Returns available sales offers without internal fields"]:
        # Filter out internal fields starting with '_'
        offers_public = {}
        for offer, details in self.offers.items():
            offers_public[offer] = {
                k: v for k, v in details.items() if not k.startswith("_")
            }
        return json.dumps(offers_public)


sales_agent = ChatCompletionAgent(
    description="A sales agent that can answer describe available offers",
    id="sales",
    name="Sales",
    service=create_service(),
    plugins=[SalesAgentPlugin()],
    instructions="""
You are a sales person that responds to customer inquiries.

Your tasks are:
- Provide the Customer with the information they need. Try to be specific and provide options that fit their needs.

# IMPORTANT NOTES
- DO act politely and professionally.
- NEVER provide false information.
""",
)
