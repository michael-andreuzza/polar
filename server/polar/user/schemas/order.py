from pydantic import UUID4, Field

from polar.kit.schemas import Schema, TimestampedSchema
from polar.product.schemas import ProductPrice, ProductSubscriber
from polar.subscription.schemas import SubscriptionBase


class UserOrderBase(TimestampedSchema):
    id: UUID4
    amount: int
    tax_amount: int
    currency: str

    user_id: UUID4
    product_id: UUID4
    product_price_id: UUID4
    subscription_id: UUID4 | None = None


class UserOrderProduct(ProductSubscriber): ...


class UserOrderSubscription(SubscriptionBase): ...


class UserOrder(UserOrderBase):
    product: UserOrderProduct
    product_price: ProductPrice
    subscription: UserOrderSubscription | None = None


class UserOrderInvoice(Schema):
    """Order's invoice data."""

    url: str = Field(..., description="The URL to the invoice.")
