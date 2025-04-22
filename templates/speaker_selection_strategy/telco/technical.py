from typing import Annotated
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.functions import kernel_function

from sk_ext.basic_kernel import create_service


class TechnicalAgentPlugin:
    @kernel_function
    def get_service_status(
        service_sku: Annotated[str, "The SKU of the service to check status for"]
    ) -> Annotated[str, "Status of the specified service"]:

        if service_sku == "INET_MOBILE":
            return "Service operational"
        elif service_sku == "INET_BUNDLE":
            return "Service degraded due to high traffic"
        elif service_sku == "INET_HOME":
            return "Service operational with occasional slow speeds"
        else:
            return "Invalid service SKU"

    @kernel_function
    def check_customer_telemetry(
        service_sku: Annotated[
            str,
            "The SKU of the service to check status for, value can be only INET_MOBILE, INET_BUNDLE, INET_HOME",
        ],
        customerCode: Annotated[str, "The customer code to check telemetry for"],
    ) -> Annotated[str, "Telemetry summary for the specified customer"]:

        if service_sku == "INET_MOBILE":
            base_telemetry = f"Customer {customerCode}: Mobile telemetry indicates user monthly data limit reached."
        elif service_sku == "INET_BUNDLE":
            base_telemetry = f"Customer {customerCode}: Bundle telemetry shows slight latency but overall stable connection."
        elif service_sku == "INET_HOME":
            base_telemetry = (
                f"Customer {customerCode}: Home telemetry reports optimal performance."
            )
        else:
            base_telemetry = f"Customer {customerCode}: Unknown service SKU provided."

        # Extra logic based on customerCode
        # Check for VIP customers (codes starting with 'VIP') for priority notices
        if customerCode.startswith("VIP"):
            extra_message = " Priority support activated."
        else:
            extra_message = ""

        # Use numeric parts of the customerCode to determine additional status
        digits = "".join(filter(str.isdigit, customerCode))
        if digits:
            if int(digits) % 2 == 0:
                digit_message = " Even numbered customer code detected: eligible for a special discount."
            else:
                digit_message = (
                    " Odd numbered customer code: standard support protocols applied."
                )
        else:
            digit_message = " No numeric identifier found in customer code; default support levels apply."

        return base_telemetry + extra_message + digit_message


technical_agent = ChatCompletionAgent(
    description="A technical support agent that can answer technical questions",
    id="technical",
    name="TechnicalSupport",
    service=create_service(),
    plugins=[TechnicalAgentPlugin()],
    instructions="""You are a technical support agent that responds to customer inquiries.

    Your task are:
    - Assess the technical issue the customer is facing.
    - Verify if there any known issues with the service the customer is using.
    - Check remote telemetry data to identify potential issues with customer's device. Be sure to ask customer code first.
    - Provide the customer with possible solutions to the issue. See the list of common issues below.
    - When the service status is OK, reply the customer and suggest to restart the device.
    - When the service status is DEGRADED, apologize to the customer and kindly ask them to wait for the issue to be resolved.
    - Open an internal ticket if the issue cannot be resolved immediately.

    Make sure to act politely and professionally.

    ### Common issues and solutions:

    - Home Internet:
        - Issue: No internet connection.
        - Solutions: 
            - Check the router's power supply and cables.
            - Restart the router.
            - Check the internet connection status LED on the router.
    - Mobile Internet:
        - Issue: Slow internet connection or no connection.
        - Solutions:
            - Check the signal strength on the device.
            - Restart the device.
            - Check the data usage on the device.
            - Suggest the customer to purchase additional data when the limit is reached.
    - All-in-One Bundle:
        USE a combination of the solutions for Home Internet and Mobile Internet.    
    """,
)
