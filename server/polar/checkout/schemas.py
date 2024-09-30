from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import UUID4, Field, IPvAnyAddress

from polar.enums import PaymentProcessor
from polar.kit.address import Address
from polar.kit.schemas import EmailStrDNS, IDSchema, Schema, TimestampedSchema
from polar.models.checkout import CheckoutStatus
from polar.product.schemas import Product, ProductPrice

Amount = Annotated[
    int,
    Field(
        description=(
            "Amount to pay in cents. "
            "Only available for custom prices, "
            "setting it for fixed or free prices will raise an error."
        )
    ),
]
CustomerName = Annotated[
    str,
    Field(description="Name of the customer."),
]
CustomerEmail = Annotated[
    EmailStrDNS,
    Field(description="Email address of the customer."),
]
CustomerIPAddress = Annotated[
    IPvAnyAddress,
    Field(
        description="IP address of the customer. Used to detect tax location.",
    ),
]
CustomerBillingAddress = Annotated[
    Address,
    Field(description="Billing address of the customer."),
]
Metadata = Annotated[
    dict[str, str],
    Field(
        description=(
            "Metadata to store with the checkout. "
            "Useful to store additional information about the checkout."
        ),
        validation_alias="user_metadata",
    ),
]


class CheckoutCreate(Schema):
    """Create a new checkout session."""

    payment_processor: Literal[PaymentProcessor.stripe] = Field(
        description="Payment processor to use. Currently only Stripe is supported."
    )
    product_price_id: UUID4 = Field(description="ID of the product price to checkout.")
    amount: Amount | None = None
    customer_name: CustomerName | None = None
    customer_email: CustomerEmail | None = None
    customer_ip_address: CustomerIPAddress | None = None
    customer_billing_address: CustomerBillingAddress | None = None
    customer_tax_id: str | None = None
    metadata: Metadata = Field(default_factory=dict)


class CheckoutUpdateBase(Schema):
    product_price_id: UUID4 | None = Field(
        default=None,
        description=(
            "ID of the product price to checkout. "
            "Must correspond to a price linked to the same product."
        ),
    )
    amount: Amount | None = None
    customer_name: CustomerName | None = None
    customer_email: CustomerEmail | None = None
    customer_ip_address: CustomerIPAddress | None = None
    customer_billing_address: CustomerBillingAddress | None = None
    customer_tax_id: str | None = None


class CheckoutUpdate(CheckoutUpdateBase):
    """Update an existing checkout session using an access token."""

    metadata: Metadata | None = None


class CheckoutUpdatePublic(CheckoutUpdateBase):
    """Update an existing checkout session using the client secret."""


class CheckoutConfirmBase(CheckoutUpdatePublic): ...


class CheckoutConfirmStripe(CheckoutConfirmBase):
    """Confirm a checkout session using a Stripe confirmation token."""

    confirmation_token_id: str = Field(
        description="ID of the Stripe confirmation token."
    )


CheckoutConfirm = CheckoutConfirmStripe


class CheckoutBase(IDSchema, TimestampedSchema):
    payment_processor: PaymentProcessor = Field(description="Payment processor used.")
    status: CheckoutStatus = Field(description="Status of the checkout session.")
    client_secret: str = Field(
        description=(
            "Client secret used to update and complete "
            "the checkout session from the client."
        )
    )
    expires_at: datetime = Field(
        description="Expiration date and time of the checkout session."
    )
    amount: Amount | None
    tax_amount: int | None = Field(description="Computed tax amount to pay in cents.")
    currency: str | None = Field(description="Currency code of the checkout session.")
    product_id: UUID4 = Field(description="ID of the product to checkout.")
    product_price_id: UUID4 = Field(description="ID of the product price to checkout.")

    customer_name: CustomerName | None
    customer_email: CustomerEmail | None
    customer_ip_address: CustomerIPAddress | None
    customer_billing_address: CustomerBillingAddress | None
    customer_tax_id: str | None = Field(validation_alias="customer_tax_id_number")

    payment_processor_metadata: dict[str, Any]


class Checkout(CheckoutBase):
    """Checkout session data retrieved using an access token."""

    metadata: Metadata


class CheckoutPublic(CheckoutBase):
    """Checkout session data retrieved using the client secret."""

    product: Product
    product_price: ProductPrice
