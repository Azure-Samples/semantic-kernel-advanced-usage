from typing import Annotated
from sk_ext.basic_kernel import create_service
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.functions import kernel_function
import json


class BillingAgentPlugin:
    def __init__(self):
        # Data persisted in memory for invoices and payment methods for customers.
        self.invoices = {
            "12345": {
                "invoice_id": "INV12345",
                "customer_id": "12345",
                "currency": "USD",
                "due_date": "2022-01-31",
                "description": "Monthly subscription billing",
                "items": [
                    {"code": "SUB", "description": "Subscription Fee", "amount": 90},
                    {"code": "TAX", "description": "Sales Tax", "amount": 10},
                ],
                "total": 100,
            },
            "67890": {
                "invoice_id": "INV67890",
                "customer_id": "67890",
                "currency": "USD",
                "due_date": "2022-02-15",
                "description": "One-time setup fee included",
                "items": [
                    {"code": "SETUP", "description": "Setup Fee", "amount": 140},
                    {"code": "TAX", "description": "Sales Tax", "amount": 10},
                ],
                "total": 150,
            },
        }
        self.payment_methods = {
            "12345": ["credit_card", "paypal", "bank_transfer"],
            "67890": ["credit_card", "bank_transfer"],
        }
        # New: Usage metrics for telco scenario (e.g., voice, data, sms)
        self.usage_metrics = {
            "12345": {
                "voice_minutes": 120,
                "data_usage_gb": 200,
                "sms": 100,
            },
            "67890": {
                "voice_minutes": 20 * 8 * 60,
                "data_usage_gb": 50.0,
                "sms": 50,
            },
        }

    @kernel_function
    def get_last_invoice(
        self,
        customer_id: Annotated[
            str, "The ID of the customer to get the last invoice for"
        ],
    ) -> Annotated[str, "The last invoice for the specified customer"]:
        invoice = self.invoices.get(customer_id)
        if invoice:
            return json.dumps(invoice)
        return '{"error": "Customer not found"}'

    @kernel_function
    def get_payment_methods(
        self,
        customer_id: Annotated[
            str, "The ID of the customer to get the payment methods for"
        ],
    ) -> Annotated[str, "The payment methods available for the specified customer"]:
        methods = self.payment_methods.get(customer_id)
        if methods:
            return json.dumps(methods)
        return '{"error": "Customer not found"}'

    @kernel_function
    def change_payment_method(
        self,
        customer_id: Annotated[
            str, "The ID of the customer to change the payment method for"
        ],
        new_method: Annotated[str, "The new payment method to set"],
    ) -> Annotated[str, "The result of changing the payment method"]:
        if customer_id in self.payment_methods:
            # If the payment method is not already listed, add it.
            if new_method not in self.payment_methods[customer_id]:
                self.payment_methods[customer_id].append(new_method)
            return f"Payment method changed to: {new_method}"
        return '{"error": "Customer not found"}'

    @kernel_function
    def get_usage_metrics(
        self,
        customer_id: Annotated[str, "The ID of the customer to get usage metrics for"],
    ) -> Annotated[
        str, "Usage metrics for telco services including voice, data, and SMS"
    ]:
        metrics = self.usage_metrics.get(customer_id)
        if metrics:
            return json.dumps(metrics)
        return '{"error": "Customer not found"}'


billing_agent = ChatCompletionAgent(
    description="A billing support agent that can answer billing-related questions, like invoices, payment methods, and usage metrics",
    id="billing",
    name="Billing",
    service=create_service(),
    plugins=[BillingAgentPlugin()],
    instructions="""
    You are a billing support agent that responds to customer inquiries.
    
    Your tasks are:
    - Retrieve the last invoice for a customer
    - Provide available payment methods for a customer
    - Change the payment method for a customer
    - Provide usage metrics for telco services (voice, data, SMS)
    - Handle disputes and billing inquiries
    - Provide billing-related information and support
    
    Rules:
    - Make sure to act politely and professionally.
    """,
)
