import os
import django
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_shop.settings')
django.setup()

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from catalog.models import Product
from orders.models import Order, OrderItem
from django.contrib.auth import get_user_model
from django.utils import timezone
from analytics.analytics import get_today_stats

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

SELECT_PRODUCT, ENTER_ADDRESS, ENTER_PHONE = range(3)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Здравствуйте! Добро пожаловать в сервис доставки цветов. "
        "Введите /order чтобы сделать заказ или /stats для отчёта (админам)."
    )

def order_start(update: Update, context: CallbackContext):
    products = Product.objects.all()
    keyboard = [[f"{p.pk} - {p.name} ({p.price}р.)"] for p in products]
    update.message.reply_text(
        "Выберите букет. Напишите номер: ",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return SELECT_PRODUCT

def select_product(update: Update, context: CallbackContext):
    try:
        product_id = int(update.message.text.split(' ')[0])
        product = Product.objects.get(pk=product_id)
        context.user_data['product'] = product
        update.message.reply_text("Введите адрес доставки:")
        return ENTER_ADDRESS
    except Exception:
        update.message.reply_text("Неверный формат. Попробуйте ещё раз.")
        return SELECT_PRODUCT

def enter_address(update: Update, context: CallbackContext):
    context.user_data['address'] = update.message.text
    update.message.reply_text("Введите телефон:")
    return ENTER_PHONE

def enter_phone(update: Update, context: CallbackContext):
    phone = update.message.text
    user_model = get_user_model()
    tg_username = update.message.from_user.username
    user, created = user_model.objects.get_or_create(
        username=f"tg_{tg_username or update.message.from_user.id}",
        defaults={'phone': phone, 'address': context.user_data['address'], 'email': f"{tg_username or update.message.from_user.id}@tg.local"}
    )
    order = Order.objects.create(
        user=user,
        status='new',
        address=context.user_data['address'],
        phone=phone,
        total=context.user_data['product'].price
    )
    OrderItem.objects.create(
        order=order,
        product=context.user_data['product'],
        quantity=1,
        price=context.user_data['product'].price
    )
    update.message.reply_text(f"Ваш заказ принят! Номер заказа: {order.pk}.\nСтатус: Новый.")
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Заказ отменён.")
    return ConversationHandler.END

def stats(update: Update, context: CallbackContext):
    admins = [int(x) for x in os.environ.get('TG_ADMINS', '').split(',') if x]
    if update.message.from_user.id not in admins:
        update.message.reply_text("Нет доступа.")
        return
    total_orders, revenue = get_today_stats()
    update.message.reply_text(f"Сегодня заказов: {total_orders}\nВыручка: {revenue} руб.")


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    conv = ConversationHandler(
        entry_points=[CommandHandler('order', order_start)],
        states={
            SELECT_PRODUCT: [MessageHandler(Filters.text & ~Filters.command, select_product)],
            ENTER_ADDRESS: [MessageHandler(Filters.text & ~Filters.command, enter_address)],
            ENTER_PHONE: [MessageHandler(Filters.text & ~Filters.command, enter_phone)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(conv)
    dp.add_handler(CommandHandler('stats', stats))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()