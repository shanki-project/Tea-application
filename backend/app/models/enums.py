"""Shared enumerations used by models and schemas."""

import enum


class UserRole(str, enum.Enum):
    super_admin = "super_admin"
    admin = "admin"  # Admin/Staff
    customer = "customer"


class OrderStatus(str, enum.Enum):
    placed = "placed"
    packed = "packed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


# Allowed forward transitions for the order-status workflow.
ORDER_STATUS_FLOW: dict[OrderStatus, list[OrderStatus]] = {
    OrderStatus.placed: [OrderStatus.packed, OrderStatus.cancelled],
    OrderStatus.packed: [OrderStatus.shipped, OrderStatus.cancelled],
    OrderStatus.shipped: [OrderStatus.delivered],
    OrderStatus.delivered: [],
    OrderStatus.cancelled: [],
}
