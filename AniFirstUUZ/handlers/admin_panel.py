from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database.db import (
    get_users_count, get_animes_count, get_all_required_channels,
    add_required_channel, remove_required_channel, toggle_required_channel,
    get_all_settings
)
from keyboards.main_kb import (
    admin_main_kb, admin_channels_kb, admin_settings_kb, back_kb, cancel_kb
)
from utils.helpers import is_admin
from utils.states import ChannelStates

router = Router(name="admin_panel")


@router.callback_query(F.data == "admin_panel")
async def cb_admin_panel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    await state.clear()
    await callback.answer()
    text = "👑 <b>Admin Panel</b>\n\nKerakli bo'limni tanlang:"
    try:
        await callback.message.edit_text(text, reply_markup=admin_main_kb())
    except Exception:
        await callback.message.answer(text, reply_markup=admin_main_kb())


@router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    await callback.answer()

    users_count = await get_users_count()
    animes_count = await get_animes_count(include_restricted=True)
    restricted_count = await get_animes_count(include_restricted=True) - await get_animes_count(include_restricted=False)

    text = (
        "📊 <b>Bot Statistikasi</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{users_count}</b>\n"
        f"🎬 Jami animalar: <b>{animes_count}</b>\n"
        f"🔒 Cheklangan animalar: <b>{restricted_count}</b>\n"
    )
    await callback.message.edit_text(text, reply_markup=back_kb("admin_panel"))


@router.callback_query(F.data == "admin_users")
async def cb_admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    await callback.answer()
    count = await get_users_count()
    text = (
        f"👥 <b>Foydalanuvchilar</b>\n\n"
        f"Jami: <b>{count}</b> ta\n\n"
        f"📢 Hammaga xabar yuborish uchun 'Post yuborish' bo'limidan foydalaning."
    )
    await callback.message.edit_text(text, reply_markup=back_kb("admin_panel"))


# ==================== MAJBURIY OBUNA KANALLARI ====================

@router.callback_query(F.data == "admin_channels")
async def cb_admin_channels(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    await callback.answer()
    channels = await get_all_required_channels()
    text = "🔗 <b>Majburiy Obuna Kanallari</b>\n\nKanalni yoqish/o'chirish uchun bosing:"
    if not channels:
        text += "\n\n📭 Hozircha kanallar qo'shilmagan."
    await callback.message.edit_text(text, reply_markup=admin_channels_kb(channels))


@router.callback_query(F.data.startswith("channel_toggle:"))
async def cb_channel_toggle(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    channel_db_id = int(callback.data.split(":")[1])
    await toggle_required_channel(channel_db_id)
    await callback.answer("✅ Holat o'zgartirildi!")
    channels = await get_all_required_channels()
    await callback.message.edit_reply_markup(reply_markup=admin_channels_kb(channels))


@router.callback_query(F.data.startswith("add_channel:"))
async def cb_add_channel_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)

    platform = callback.data.split(":")[1]

    if platform == "youtube":
        existing = await get_all_required_channels()
        yt_count = len([c for c in existing if c["platform"] == "youtube"])
        if yt_count >= 2:
            return await callback.answer(
                "⚠️ YouTube uchun maksimal 2 ta kanal qo'shish mumkin!", show_alert=True
            )

    await callback.answer()
    await state.update_data(platform=platform)
    await state.set_state(ChannelStates.waiting_name)

    platform_names = {"telegram": "Telegram", "instagram": "Instagram", "youtube": "YouTube"}
    await callback.message.answer(
        f"➕ <b>{platform_names.get(platform, platform)} kanal qo'shish</b>\n\n"
        f"Kanal nomini kiriting (masalan: 'Asosiy kanal'):",
        reply_markup=cancel_kb()
    )


@router.message(ChannelStates.waiting_name)
async def channel_name_received(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())

    await state.update_data(channel_name=message.text)
    data = await state.get_data()
    platform = data["platform"]

    await state.set_state(ChannelStates.waiting_link)
    if platform == "telegram":
        await message.answer(
            "🔗 Kanal linkini kiriting (masalan: https://t.me/kanal_nomi):"
        )
    else:
        await message.answer(
            f"🔗 {platform.capitalize()} profil/kanal linkini kiriting:"
        )


@router.message(ChannelStates.waiting_link)
async def channel_link_received(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())

    await state.update_data(channel_link=message.text)
    data = await state.get_data()
    platform = data["platform"]

    if platform == "telegram":
        await state.set_state(ChannelStates.waiting_id)
        await message.answer(
            "🆔 Kanal ID raqamini kiriting (masalan: -1001234567890).\n\n"
            "💡 ID ni bilish uchun botni kanalga admin qilib, "
            "@userinfobot orqali kanal postini forward qiling.\n\n"
            "Agar ID kiritmoqchi bo'lmasangiz, 'o'tkazib yuborish' deb yozing."
        )
    else:
        # Instagram/YouTube uchun real tekshirish yo'q, faqat link saqlanadi
        await save_channel(message, state)


@router.message(ChannelStates.waiting_id)
async def channel_id_received(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())

    channel_id = None if "o'tkazib" in message.text.lower() else message.text.strip()
    await state.update_data(channel_id=channel_id)
    await save_channel(message, state)


async def save_channel(message: Message, state: FSMContext):
    data = await state.get_data()
    success, msg = await add_required_channel(
        platform=data["platform"],
        channel_link=data["channel_link"],
        channel_name=data["channel_name"],
        channel_id=data.get("channel_id"),
    )
    await state.clear()

    if success:
        await message.answer(f"✅ {msg}", reply_markup=admin_main_kb())
    else:
        await message.answer(f"❌ {msg}", reply_markup=admin_main_kb())


@router.callback_query(F.data == "delete_channel_select")
async def cb_delete_channel_select(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    await callback.answer()

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    channels = await get_all_required_channels()
    if not channels:
        return await callback.message.edit_text(
            "📭 O'chirish uchun kanallar yo'q.", reply_markup=back_kb("admin_channels")
        )

    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.row(InlineKeyboardButton(
            text=f"🗑️ {ch['channel_name']}", callback_data=f"channel_delete:{ch['id']}"
        ))
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_channels"))

    await callback.message.edit_text(
        "🗑️ O'chirish uchun kanalni tanlang:", reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("channel_delete:"))
async def cb_channel_delete(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    channel_db_id = int(callback.data.split(":")[1])
    await remove_required_channel(channel_db_id)
    await callback.answer("✅ Kanal o'chirildi!")
    channels = await get_all_required_channels()
    await callback.message.edit_text(
        "🔗 <b>Majburiy Obuna Kanallari</b>", reply_markup=admin_channels_kb(channels)
    )
