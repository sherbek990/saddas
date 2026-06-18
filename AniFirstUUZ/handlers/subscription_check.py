from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.db import get_required_channels, get_setting
from keyboards.main_kb import main_menu_kb, subscription_check_kb
from utils.helpers import is_admin

router = Router(name="subscription_check")


@router.callback_query(F.data == "check_subscription")
async def check_subscription(callback: CallbackQuery):
    user_id = callback.from_user.id

    if is_admin(user_id):
        await callback.message.delete()
        await callback.message.answer("✅ Tasdiqlandi!", reply_markup=main_menu_kb())
        return

    sub_required = await get_setting("subscription_required", "1")
    if sub_required != "1":
        await callback.message.delete()
        await callback.message.answer("✅ Tasdiqlandi!", reply_markup=main_menu_kb())
        return

    channels = await get_required_channels("telegram")
    not_subscribed = []

    for ch in channels:
        if not ch.get("channel_id"):
            continue
        try:
            member = await callback.bot.get_chat_member(
                chat_id=ch["channel_id"], user_id=user_id
            )
            if member.status in ("left", "kicked"):
                not_subscribed.append(ch)
        except Exception:
            continue

    if not_subscribed:
        await callback.answer("❌ Siz hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
        return

    await callback.answer("✅ Obuna tasdiqlandi!", show_alert=True)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "✅ Rahmat! Endi botdan to'liq foydalanishingiz mumkin.",
        reply_markup=main_menu_kb()
    )
