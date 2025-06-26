from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import OrderCreateForm
from catalog.models import Product
from .models import Order, OrderItem
from django.utils import timezone
from datetime import time

def check_working_hours():
    now = timezone.localtime()
    if now.weekday() == 6:  # Sunday
        return False
    start = time(9, 0)
    end = time(19, 0)
    return start <= now.time() <= end

@login_required
def order_create(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('cart')
    if not check_working_hours():
        return render(request, 'orders/order_create.html', {'error': 'Заказы принимаются только в рабочее время (09:00-19:00, воскресенье — выходной).'})

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            address = form.cleaned_data['address']
            phone = form.cleaned_data['phone']
            products = Product.objects.filter(pk__in=cart.keys())
            total = 0
            for product in products:
                quantity = cart[str(product.pk)]
                total += product.price * quantity
            order = Order.objects.create(
                user=request.user,
                address=address,
                phone=phone,
                total=total,
                status='new'
            )
            for product in products:
                quantity = cart[str(product.pk)]
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price
                )
            request.session['cart'] = {}
            return redirect('order_detail', pk=order.pk)
    else:
        form = OrderCreateForm(initial={'address': request.user.address, 'phone': request.user.phone})
    return render(request, 'orders/order_create.html', {'form': form})

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required
def order_repeat(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    cart = {}
    for item in order.items.all():
        cart[str(item.product.pk)] = item.quantity
    request.session['cart'] = cart
    return redirect('cart')
