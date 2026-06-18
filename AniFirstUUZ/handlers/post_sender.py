import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from database.db import (
    get_all_users, get_broadcast_channels, add_broadcast_channel,
    remove_broadcast_channel, get_all_animes, get_animes_count, get_anime
)
from keyboards.main_kb import admin_post_kb, admin_main_kb, cancel_kb, back_kb, post_anime_select_kb
from utils.helpers import is_admin
from utils.states import PostStates

router = Router(name="post_sender")

ANIME_PER_PAGE = 8


@router.callback_query(F.data == "admin_post")
async def cb_admin_post(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(
        "📤 <b>Post Yuborish</b>\n\nQanday turdagi post yubormoqchisiz?",
        reply_markup=admin_post_kb()
    )


# ==================== HAMMAGA XABAR (BROADCAST) ====================

@router.callback_query(F.data == "broadcast_all")
async def cb_broadcast_all_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    await callback.answer()
    await state.set_state(PostStates.waiting_broadcast_text)
    await callback.message.answer(
        "📢 <b>Hammaga Xabar Yuborish</b>\n\n"
        "Yubormoqchi bo'lgan xabarni yozing (matn, rasm, video bo'lishi mumkin):",
        reply_markup=cancel_kb()
    )


@router.message(PostStates.waiting_broadcast_text)
async def broadcast_message_received(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())

    await state.clear()
    users = await get_all_users()
    status_msg = await message.answer(f"⏳ Yuborilmoqda... (0/{len(users)})")

    sent, failed = 0, 0
    for i, user in enumerate(users, start=1):
        try:
            await message.copy_to(chat_id=user["user_id"])
            sent += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
        except Exception:
            failed += 1

        if i % 25 == 0:
            try:
                await status_msg.edit_text(f"⏳ Yuborilmoqda... ({i}/{len(users)})")
            except Exception:
                pass
            await asyncio.sleep(0.05)

    await status_msg.edit_text(
        f"✅ <b>Xabar yuborish yakunlandi!</b>\n\n"
        f"✅ Yuborildi: {sent}\n"
        f"❌ Yuborilmadi: {failed}"
    )
    await message.answer("Admin panelga qaytish:", reply_markup=admin_main_kb())


# ==================== POST YUBORISH (BIR NECHTA KANALGA) ====================

@router.callback_query(F.data.in_({"post_text", "post_photo", "post_video"}))
async def cb_post_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)

    channels = await get_broadcast_channels()
    if not channels:
        await callback.answer()
        return await callback.message.answer(
            "⚠️ Hozircha kanallar qo'shilmagan!\n\n"
            "Avval /addchannel buyrug'i bilan kanal qo'shing, yoki botni kanalga "
            "admin qilib, kanaldan biror xabarni shu botga forward qiling.",
            reply_markup=back_kb("admin_post")
        )

    post_type = callback.data.split("_")[1]  # text, photo, video
    await state.update_data(post_type=post_type)
    await callback.answer()
    await state.set_state(PostStates.waiting_anime_choice)
    await render_post_anime_select(callback, page=1)


async def render_post_anime_select(callback: CallbackQuery, page: int):
    total = await get_animes_count(include_restricted=True)
    animes = await get_all_animes(page=page, per_page=ANIME_PER_PAGE, restricted_for_admin=True)
    text = (
        "🔗 <b>Postni animega bog'lash</b>\n\n"
        "Agar shu postni qaysi anime haqida ekanini tanlasangiz, post tagida "
        "\"▶️ Tomosha qilish\" tugmasi qo'shiladi va u botga ushbu anime sahifasiga "
        "deep link orqali olib boradi.\n\n"
        "Animani tanlang yoki havolasiz yuboring:"
    )
    kb = post_anime_select_kb(animes, page=page, total=total, per_page=ANIME_PER_PAGE)
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.answer(text, reply_markup=kb)


@router.callback_query(PostStates.waiting_anime_choice, F.data.startswith("post_anime_page:"))
async def cb_post_anime_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await callback.answer()
    await render_post_anime_select(callback, page=page)


@router.callback_query(PostStates.waiting_anime_choice, F.data.startswith("post_select_anime:"))
async def cb_post_select_anime(callback: CallbackQuery, state: FSMContext):
    anime_id = int(callback.data.split(":")[1])
    anime = await get_anime(anime_id)
    if not anime:
        return await callback.answer("Anime topilmadi!", show_alert=True)

    await state.update_data(anime_id=anime_id)
    await callback.answer()
    await ask_for_post_content(callback.message, state)


@router.callback_query(PostStates.waiting_anime_choice, F.data == "post_no_anime")
async def cb_post_no_anime(callback: CallbackQuery, state: FSMContext):
    await state.update_data(anime_id=None)
    await callback.answer()
    await ask_for_post_content(callback.message, state)


async def ask_for_post_content(message: Message, state: FSMContext):
    data = await state.get_data()
    post_type = data.get("post_type", "text")
    await state.set_state(PostStates.waiting_text)

    type_labels = {"text": "📝 Matn", "photo": "🖼️ Rasm + Matn (caption bilan)", "video": "🎬 Video + Matn (caption bilan)"}
    await message.answer(
        f"{type_labels[post_type]} yuboring (men buni barcha ulangan kanallarga yuboraman):",
        reply_markup=cancel_kb()
    )


@router.message(PostStates.waiting_text)
async def post_content_received(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())

    data = await state.get_data()
    post_type = data.get("post_type", "text")
    anime_id = data.get("anime_id")

    if post_type == "photo" and not message.photo:
        return await message.answer("⚠️ Iltimos rasm yuboring.")
    if post_type == "video" and not message.video:
        return await message.answer("⚠️ Iltimos video yuboring.")

    channels = await get_broadcast_channels()
    await state.clear()

    watch_kb = None
    if anime_id:
        anime = await get_anime(anime_id)
        if anime:
            me = await message.bot.get_me()
            deep_link = f"https://t.me/{me.username}?start=anime_{anime_id}"
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="▶️ Tomosha qilish", url=deep_link))
            watch_kb = builder.as_markup()

    status_msg = await message.answer(f"⏳ {len(channels)} ta kanalga yuborilmoqda...")

    sent, failed = 0, []
    for ch in channels:
        try:
            await message.copy_to(chat_id=ch["channel_id"], reply_markup=watch_kb)
            sent += 1
        except Exception as e:
            failed.append(f"{ch['channel_name']} ({e.__class__.__name__})")

    result_text = f"✅ <b>Post yuborildi!</b>\n\n✅ Muvaffaqiyatli: {sent}/{len(channels)}"
    if failed:
        result_text += "\n\n❌ Xatoliklar:\n" + "\n".join(f"• {f}" for f in failed)

    await status_msg.edit_text(result_text)
    await message.answer("Admin panelga qaytish:", reply_markup=admin_main_kb())


# ==================== POST UCHUN KANALLARNI BOSHQARISH ====================

@router.callback_query(F.data == "admin_broadcast_channels")
async def cb_broadcast_channels_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    await callback.answer()

    channels = await get_broadcast_channels()
    text = "📡 <b>Post Yuborish Kanallari</b>\n\n"
    if channels:
        text += "Hozirgi kanallar:\n" + "\n".join(
            f"• {ch['channel_name']} (<code>{ch['channel_id']}</code>)" for ch in channels
        )
    else:
        text += "📭 Hozircha kanallar qo'shilmagan."

    text += (
        "\n\n➕ <b>Kanal qo'shish uchun:</b>\n"
        "1. Botni kanalga <b>admin</b> qilib qo'shing\n"
        "2. Kanaldan istalgan postni shu botga <b>forward</b> qiling\n"
        "Bot avtomatik o'sha kanalni ro'yxatga qo'shadi."
    )

    await callback.message.edit_text(text, reply_markup=back_kb("admin_panel"))


@router.message(F.forward_from_chat)
async def auto_add_broadcast_channel(message: Message):
    if not is_admin(message.from_user.id):
        return

    chat = message.forward_from_chat
    if chat.type != "channel":
        return

    success = await add_broadcast_channel(channel_id=str(chat.id), channel_name=chat.title)
    if success:
        await message.answer(
            f"✅ <b>{chat.title}</b> kanali post yuborish ro'yxatiga qo'shildi!"
        )
    else:
        await message.answer(f"ℹ️ <b>{chat.title}</b> kanali allaqachon ro'yxatda mavjud.")
