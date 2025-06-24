from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from orders.models import Order
from django.db.models import Sum, Count
from django.utils import timezone

@staff_member_required
def report(request):
    today = timezone.localdate()
    orders_today = Order.objects.filter(created_at__date=today)
    total_orders = orders_today.count()
    revenue = orders_today.aggregate(total=Sum('total'))['total'] or 0
    return render(request, 'analytics/report.html', {
        'total_orders': total_orders,
        'revenue': revenue,
        'orders_today': orders_today,
        'today': today,
    })
