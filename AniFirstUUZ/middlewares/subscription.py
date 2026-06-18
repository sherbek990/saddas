from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

from database.db import get_required_channels, get_setting
from utils.helpers import is_admin
from keyboards.main_kb import subscription_check_kb


class SubscriptionMiddleware(BaseMiddleware):
    """
    Har bir update kelganda foydalanuvchining majburiy kanallarga
    obuna bo'lganligini tekshiradi. Adminlar va sozlama o'chirilgan
    bo'lsa tekshirishdan o'tkazib yuboriladi.
    """

    # Tekshirishdan ozod qilinadigan callback'lar
    EXEMPT_CALLBACKS = {"check_subscription"}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        # Adminlar uchun tekshirish shart emas
        if is_admin(user.id):
            return await handler(event, data)

        # Sozlamada majburiy obuna o'chirilgan bo'lsa
        sub_required = await get_setting("subscription_required", "1")
        if sub_required != "1":
            return await handler(event, data)

        # Callback bo'lsa va istisno ro'yxatida bo'lsa, davom etamiz
        if isinstance(event, CallbackQuery) and event.data in self.EXEMPT_CALLBACKS:
            return await handler(event, data)

        # Faqat Telegram kanallarni real tekshiramiz (bot orqali)
        channels = await get_required_channels("telegram")
        if not channels:
            return await handler(event, data)

        bot = data.get("bot")
        not_subscribed = []
        for ch in channels:
            if not ch.get("channel_id"):
                continue
            try:
                member = await bot.get_chat_member(chat_id=ch["channel_id"], user_id=user.id)
                if member.status in ("left", "kicked"):
                    not_subscribed.append(ch)
            except Exception:
                # Bot kanalda admin bo'lmasa yoki xatolik bo'lsa, o'tkazib yuboramiz
                continue

        if not_subscribed:
            all_channels = await get_required_channels()
            kb = subscription_check_kb(all_channels)
            text = (
                "⚠️ <b>Majburiy Obuna!</b>\n\n"
                "Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling, "
                "so'ngra <b>✅ Tekshirish</b> tugmasini bosing:"
            )
            if isinstance(event, Message):
                await event.answer(text, reply_markup=kb)
            elif isinstance(event, CallbackQuery):
                await event.answer()
                await event.message.answer(text, reply_markup=kb)
            return

        return await handler(event, data)
