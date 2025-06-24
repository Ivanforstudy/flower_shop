from orders.models import Order
from django.utils import timezone

def get_today_stats():
    today = timezone.localdate()
    orders = Order.objects.filter(created_at__date=today)
    return orders.count(), sum(order.total for order in orders)