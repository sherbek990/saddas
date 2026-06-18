from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database.db import (
    get_all_animes, get_animes_count, get_anime, add_anime, update_anime,
    delete_anime, restrict_anime, add_episode, get_episodes, get_episode,
    update_episode, delete_episode
)
from keyboards.main_kb import (
    admin_anime_list_kb, admin_anime_detail_kb, admin_anime_edit_kb,
    admin_episode_list_kb, admin_episode_edit_kb, admin_main_kb,
    confirm_kb, back_kb, cancel_kb
)
from utils.helpers import is_admin
from utils.states import AnimeStates, AnimeEditStates, EpisodeStates, EpisodeEditStates

router = Router(name="anime_manage")

PER_PAGE = 8


# ==================== ANIME RO'YXATI (ADMIN) ====================

@router.callback_query(F.data == "admin_animes")
async def cb_admin_animes(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    await state.clear()
    await callback.answer()
    await render_admin_anime_list(callback, page=1)


async def render_admin_anime_list(callback: CallbackQuery, page: int):
    total = await get_animes_count(include_restricted=True)
    animes = await get_all_animes(page=page, per_page=PER_PAGE, restricted_for_admin=True)
    text = f"🎬 <b>Anime Boshqaruvi</b> (jami: {total})"
    kb = admin_anime_list_kb(animes, page=page, total=total, per_page=PER_PAGE)
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("admin_animes_page:"))
async def cb_admin_animes_page(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    page = int(callback.data.split(":")[1])
    await callback.answer()
    await render_admin_anime_list(callback, page=page)


# ==================== YANGI ANIME QO'SHISH ====================

@router.callback_query(F.data == "admin_anime_add")
async def cb_anime_add_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    await callback.answer()
    await state.set_state(AnimeStates.waiting_title)
    await callback.message.answer(
        "➕ <b>Yangi Anime Qo'shish</b>\n\n📝 Anime nomini kiriting:",
        reply_markup=cancel_kb()
    )


@router.message(AnimeStates.waiting_title)
async def anime_title_received(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())

    await state.update_data(title=message.text)
    await state.set_state(AnimeStates.waiting_fanadub_name)
    await message.answer(
        "🎌 <b>Fanadub nomi</b>ni kiriting (qaysi fandub guruh tarjima qilgan):\n\n"
        "Agar bo'lmasa, 'yo'q' deb yozing."
    )


@router.message(AnimeStates.waiting_fanadub_name)
async def anime_fanadub_received(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())

    fanadub = None if message.text.strip().lower() in ("yo'q", "yoq", "-") else message.text
    await state.update_data(fanadub_name=fanadub)
    await state.set_state(AnimeStates.waiting_description)
    await message.answer("📄 Anime tavsifini kiriting (yoki 'yo'q'):")


@router.message(AnimeStates.waiting_description)
async def anime_description_received(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())

    desc = None if message.text.strip().lower() in ("yo'q", "yoq", "-") else message.text
    await state.update_data(description=desc)
    await state.set_state(AnimeStates.waiting_genre)
    await message.answer("🏷️ Janrini kiriting (masalan: Action, Romance):")


@router.message(AnimeStates.waiting_genre)
async def anime_genre_received(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())

    await state.update_data(genre=message.text)
    await state.set_state(AnimeStates.waiting_poster)
    await message.answer("🖼️ Anime posterini (rasm) yuboring, yoki 'yo'q' deb yozing:")


@router.message(AnimeStates.waiting_poster, F.photo)
async def anime_poster_received(message: Message, state: FSMContext):
    poster_file_id = message.photo[-1].file_id
    await finalize_anime_creation(message, state, poster_file_id)


@router.message(AnimeStates.waiting_poster, F.text)
async def anime_poster_skipped(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
    await finalize_anime_creation(message, state, None)


async def finalize_anime_creation(message: Message, state: FSMContext, poster_file_id):
    data = await state.get_data()
    anime_id = await add_anime(
        title=data["title"],
        fanadub_name=data.get("fanadub_name"),
        description=data.get("description"),
        genre=data.get("genre"),
        poster_file_id=poster_file_id,
    )
    await state.clear()

    text = (
        f"✅ <b>Anime muvaffaqiyatli qo'shildi!</b>\n\n"
        f"🎬 Nomi: {data['title']}\n"
        f"🎌 Fanadub: {data.get('fanadub_name') or '-'}\n"
        f"🏷️ Janr: {data.get('genre') or '-'}\n\n"
        f"Endi unga epizod (video) qo'shishingiz mumkin."
    )
    from keyboards.main_kb import admin_anime_detail_kb
    anime = await get_anime(anime_id)
    await message.answer(
        text, reply_markup=admin_anime_detail_kb(anime_id, anime.get("is_restricted", 0))
    )


# ==================== ANIME DETAL / TAHRIRLASH ====================

@router.callback_query(F.data.startswith("admin_anime_detail:"))
async def cb_anime_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    anime_id = int(callback.data.split(":")[1])
    anime = await get_anime(anime_id)
    if not anime:
        return await callback.answer("Topilmadi!", show_alert=True)

    await callback.answer()
    episodes = await get_episodes(anime_id)
    from utils.helpers import format_anime_caption
    text = format_anime_caption(anime) + f"\n📺 Epizodlar soni: {len(episodes)}"
    kb = admin_anime_detail_kb(anime_id, bool(anime.get("is_restricted")))

    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("admin_anime_edit:"))
async def cb_anime_edit_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    anime_id = int(callback.data.split(":")[1])
    await callback.answer()
    await callback.message.edit_text(
        "✏️ <b>Qaysi maydonni tahrirlamoqchisiz?</b>",
        reply_markup=admin_anime_edit_kb(anime_id)
    )


@router.callback_query(F.data.startswith("anime_edit_field:"))
async def cb_anime_edit_field(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)

    _, anime_id, field = callback.data.split(":")
    anime_id = int(anime_id)
    await state.update_data(anime_id=anime_id, field=field)
    await callback.answer()

    field_labels = {
        "title": "📝 Yangi nomini",
        "fanadub_name": "🎌 Yangi fanadub nomini",
        "description": "📄 Yangi tavsifni",
        "genre": "🏷️ Yangi janrni",
        "status": "📊 Yangi statusni (ongoing/completed)",
        "poster": "🖼️ Yangi posterni (rasm)",
    }

    await state.set_state(AnimeEditStates.waiting_value)

    if field == "poster":
        await callback.message.answer(f"{field_labels[field]} yuboring:", reply_markup=cancel_kb())
    else:
        await callback.message.answer(f"{field_labels.get(field, field)} kiriting:", reply_markup=cancel_kb())


@router.message(AnimeEditStates.waiting_value, F.photo)
async def anime_edit_photo_received(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("field") != "poster":
        return
    await update_anime(data["anime_id"], poster_file_id=message.photo[-1].file_id)
    await state.clear()
    anime = await get_anime(data["anime_id"])
    await message.answer(
        "✅ Poster yangilandi!",
        reply_markup=admin_anime_detail_kb(data["anime_id"], bool(anime.get("is_restricted")))
    )


@router.message(AnimeEditStates.waiting_value, F.text)
async def anime_edit_value_received(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())

    data = await state.get_data()
    field = data["field"]
    anime_id = data["anime_id"]

    if field == "poster":
        return await message.answer("⚠️ Iltimos rasm yuboring.")

    await update_anime(anime_id, **{field: message.text})
    await state.clear()

    anime = await get_anime(anime_id)
    await message.answer(
        "✅ Muvaffaqiyatli yangilandi!",
        reply_markup=admin_anime_detail_kb(anime_id, bool(anime.get("is_restricted")))
    )


# ==================== ANIME CHEKLASH / RUXSAT ====================

@router.callback_query(F.data.startswith("admin_anime_restrict:"))
async def cb_anime_restrict_toggle(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    anime_id = int(callback.data.split(":")[1])
    anime = await get_anime(anime_id)
    if not anime:
        return await callback.answer("Topilmadi!", show_alert=True)

    new_state = not bool(anime.get("is_restricted"))
    await restrict_anime(anime_id, new_state)
    await callback.answer("🔒 Cheklandi!" if new_state else "🔓 Ruxsat berildi!")

    anime = await get_anime(anime_id)
    from utils.helpers import format_anime_caption
    episodes = await get_episodes(anime_id)
    text = format_anime_caption(anime) + f"\n📺 Epizodlar soni: {len(episodes)}"
    await callback.message.edit_text(
        text, reply_markup=admin_anime_detail_kb(anime_id, bool(anime.get("is_restricted")))
    )


# ==================== ANIME O'CHIRISH ====================

@router.callback_query(F.data.startswith("admin_anime_delete_confirm:"))
async def cb_anime_delete_confirm(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    anime_id = int(callback.data.split(":")[1])
    await callback.answer()
    await callback.message.edit_text(
        "⚠️ Haqiqatan ham bu animeni butunlay o'chirib tashlamoqchimisiz?\n"
        "(Barcha epizodlari bilan birga o'chiriladi)",
        reply_markup=confirm_kb("anime_delete", anime_id)
    )


@router.callback_query(F.data.startswith("confirm_anime_delete:"))
async def cb_anime_delete_do(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    anime_id = int(callback.data.split(":")[1])
    await delete_anime(anime_id)
    await callback.answer("🗑️ O'chirildi!")
    await render_admin_anime_list(callback, page=1)


@router.callback_query(F.data.startswith("cancel_anime_delete:"))
async def cb_anime_delete_cancel(callback: CallbackQuery):
    anime_id = int(callback.data.split(":")[1])
    await callback.answer("Bekor qilindi.")
    anime = await get_anime(anime_id)
    from utils.helpers import format_anime_caption
    episodes = await get_episodes(anime_id)
    text = format_anime_caption(anime) + f"\n📺 Epizodlar soni: {len(episodes)}"
    await callback.message.edit_text(
        text, reply_markup=admin_anime_detail_kb(anime_id, bool(anime.get("is_restricted")))
    )


# ==================== EPIZOD (VIDEO) QO'SHISH ====================

@router.callback_query(F.data.startswith("admin_episode_add:"))
async def cb_episode_add_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    anime_id = int(callback.data.split(":")[1])
    await state.update_data(anime_id=anime_id)
    await state.set_state(EpisodeStates.waiting_number)
    await callback.answer()
    await callback.message.answer(
        "📹 <b>Video orqali Anime qo'shish</b>\n\n🔢 Epizod raqamini kiriting:",
        reply_markup=cancel_kb()
    )


@router.message(EpisodeStates.waiting_number)
async def episode_number_received(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())

    if not message.text.strip().isdigit():
        return await message.answer("⚠️ Iltimos faqat raqam kiriting.")

    await state.update_data(episode_number=int(message.text.strip()))
    await state.set_state(EpisodeStates.waiting_title)
    await message.answer("📝 Epizod sarlavhasini kiriting (yoki 'yo'q'):")


@router.message(EpisodeStates.waiting_title)
async def episode_title_received(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())

    title = None if message.text.strip().lower() in ("yo'q", "yoq", "-") else message.text
    await state.update_data(ep_title=title)
    await state.set_state(EpisodeStates.waiting_video)
    await message.answer("🎬 Endi videoni yuboring:")


@router.message(EpisodeStates.waiting_video, F.video)
async def episode_video_received(message: Message, state: FSMContext):
    await state.update_data(video_file_id=message.video.file_id)
    await state.set_state(EpisodeStates.waiting_thumbnail)
    await message.answer(
        "🖼️ Video uchun thumbnail (preview rasm) yuboring, yoki 'yo'q' deb yozing:"
    )


@router.message(EpisodeStates.waiting_video, F.text)
async def episode_video_skip_check(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
    await message.answer("⚠️ Iltimos video fayl yuboring.")


@router.message(EpisodeStates.waiting_thumbnail, F.photo)
async def episode_thumbnail_received(message: Message, state: FSMContext):
    await finalize_episode(message, state, message.photo[-1].file_id)


@router.message(EpisodeStates.waiting_thumbnail, F.text)
async def episode_thumbnail_skipped(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
    await finalize_episode(message, state, None)


async def finalize_episode(message: Message, state: FSMContext, thumbnail_file_id):
    data = await state.get_data()
    await add_episode(
        anime_id=data["anime_id"],
        episode_number=data["episode_number"],
        title=data.get("ep_title"),
        video_file_id=data["video_file_id"],
        thumbnail_file_id=thumbnail_file_id,
    )
    await state.clear()

    anime = await get_anime(data["anime_id"])
    await message.answer(
        f"✅ <b>{data['episode_number']}-qism muvaffaqiyatli qo'shildi!</b>",
        reply_markup=admin_anime_detail_kb(data["anime_id"], bool(anime.get("is_restricted")))
    )


# ==================== EPIZODLARNI BOSHQARISH ====================

@router.callback_query(F.data.startswith("admin_episodes:"))
async def cb_admin_episodes(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    anime_id = int(callback.data.split(":")[1])
    episodes = await get_episodes(anime_id)
    await callback.answer()

    if not episodes:
        return await callback.message.edit_text(
            "📭 Hozircha epizodlar yo'q.",
            reply_markup=admin_episode_list_kb([], anime_id)
        )

    await callback.message.edit_text(
        f"📺 <b>Epizodlar</b> (jami: {len(episodes)})\n\nTahrirlash uchun tanlang:",
        reply_markup=admin_episode_list_kb(episodes, anime_id)
    )


@router.callback_query(F.data.startswith("admin_episode_edit:"))
async def cb_episode_edit_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    episode_id = int(callback.data.split(":")[1])
    episode = await get_episode(episode_id)
    if not episode:
        return await callback.answer("Topilmadi!", show_alert=True)

    await callback.answer()
    text = f"📹 <b>{episode['episode_number']}-qism</b>"
    if episode.get("title"):
        text += f" - {episode['title']}"

    await callback.message.edit_text(
        text, reply_markup=admin_episode_edit_kb(episode_id, episode["anime_id"])
    )


@router.callback_query(F.data.startswith("ep_edit_video:"))
async def cb_ep_edit_video_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    episode_id = int(callback.data.split(":")[1])
    await state.update_data(episode_id=episode_id)
    await state.set_state(EpisodeEditStates.waiting_video)
    await callback.answer()
    await callback.message.answer("🎬 Yangi videoni yuboring:", reply_markup=cancel_kb())


@router.message(EpisodeEditStates.waiting_video, F.video)
async def ep_edit_video_received(message: Message, state: FSMContext):
    data = await state.get_data()
    await update_episode(data["episode_id"], video_file_id=message.video.file_id)
    episode = await get_episode(data["episode_id"])
    await state.clear()
    await message.answer(
        "✅ Video muvaffaqiyatli almashtirildi!",
        reply_markup=admin_episode_edit_kb(data["episode_id"], episode["anime_id"])
    )


@router.callback_query(F.data.startswith("ep_edit_thumb:"))
async def cb_ep_edit_thumb_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    episode_id = int(callback.data.split(":")[1])
    await state.update_data(episode_id=episode_id)
    await state.set_state(EpisodeEditStates.waiting_thumbnail)
    await callback.answer()
    await callback.message.answer("🖼️ Yangi thumbnail rasmni yuboring:", reply_markup=cancel_kb())


@router.message(EpisodeEditStates.waiting_thumbnail, F.photo)
async def ep_edit_thumb_received(message: Message, state: FSMContext):
    data = await state.get_data()
    await update_episode(data["episode_id"], thumbnail_file_id=message.photo[-1].file_id)
    episode = await get_episode(data["episode_id"])
    await state.clear()
    await message.answer(
        "✅ Thumbnail muvaffaqiyatli yangilandi!",
        reply_markup=admin_episode_edit_kb(data["episode_id"], episode["anime_id"])
    )


@router.callback_query(F.data.startswith("ep_edit_title:"))
async def cb_ep_edit_title_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    episode_id = int(callback.data.split(":")[1])
    await state.update_data(episode_id=episode_id)
    await state.set_state(EpisodeEditStates.waiting_title)
    await callback.answer()
    await callback.message.answer("📝 Yangi sarlavhani kiriting:", reply_markup=cancel_kb())


@router.message(EpisodeEditStates.waiting_title)
async def ep_edit_title_received(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())

    data = await state.get_data()
    await update_episode(data["episode_id"], title=message.text)
    episode = await get_episode(data["episode_id"])
    await state.clear()
    await message.answer(
        "✅ Sarlavha yangilandi!",
        reply_markup=admin_episode_edit_kb(data["episode_id"], episode["anime_id"])
    )


@router.callback_query(F.data.startswith("ep_delete_confirm:"))
async def cb_ep_delete_confirm(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    episode_id = int(callback.data.split(":")[1])
    await callback.answer()
    await callback.message.edit_text(
        "⚠️ Bu epizodni o'chirishni tasdiqlaysizmi?",
        reply_markup=confirm_kb("ep_delete", episode_id)
    )


@router.callback_query(F.data.startswith("confirm_ep_delete:"))
async def cb_ep_delete_do(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    episode_id = int(callback.data.split(":")[1])
    episode = await get_episode(episode_id)
    anime_id = episode["anime_id"]
    await delete_episode(episode_id)
    await callback.answer("🗑️ O'chirildi!")

    episodes = await get_episodes(anime_id)
    await callback.message.edit_text(
        f"📺 <b>Epizodlar</b> (jami: {len(episodes)})",
        reply_markup=admin_episode_list_kb(episodes, anime_id)
    )


@router.callback_query(F.data.startswith("cancel_ep_delete:"))
async def cb_ep_delete_cancel(callback: CallbackQuery):
    episode_id = int(callback.data.split(":")[1])
    episode = await get_episode(episode_id)
    await callback.answer("Bekor qilindi.")
    await callback.message.edit_text(
        f"📹 <b>{episode['episode_number']}-qism</b>",
        reply_markup=admin_episode_edit_kb(episode_id, episode["anime_id"])
    )
