from typing import Annotated
from sk_ext.basic_kernel import create_service
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai import (
    FunctionChoiceBehavior,
)
from semantic_kernel.functions import kernel_function


class AuthAgentPlugin:

    @kernel_function
    def check_auth(
        self,
        email: Annotated[str, "The customer's email address"],
        otp: Annotated[str, "The OTP code to authenticate"],
    ) -> Annotated[
        str,
        "Returns 'OK' with user-id if the authentication is successful, or 'ERROR' and the error message",
    ]:
        # In a real-world scenario, this would involve calling an external service
        if email == "foo@bar.com" and otp == "1234":
            return "OK; user-id=67890"
        else:
            return "ERROR; Invalid email or OTP code."


auth_agent = ChatCompletionAgent(
    description="""
An agent that can validate a user's identity using email and OTP code.
NOTE: another agent must be called to acquire the email and OTP code.
""",
    id="auth",
    name="Auth",
    service=create_service(),
    plugins=[AuthAgentPlugin()],
    function_choice_behavior=FunctionChoiceBehavior.Auto(),
    instructions="""
You are an authentication agent that helps customers confirm their identity.

Your tasks are:
- Confirm the customer's identity by asking for their email address and OTP code.
- If the authentication is successful, include a context variable 'user-id' with the retrieved value, as shown in the example below.
- NEVER try to authenticate is user did not provide all the required information.
- DO split the response into two parts: the first part is the message to the user, and the second part is the context variable. USe ~~~context~~~ as the separator.

## SUCCESS EXAMPLE
Authentication successful.

~~~context~~~
user-id=123456
""",
)
