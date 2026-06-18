from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from database.db import (
    get_all_animes, get_animes_count, get_anime,
    get_episodes, get_episode
)
from keyboards.main_kb import (
    anime_list_kb, anime_view_kb, episodes_kb,
    episode_nav_kb, main_menu_kb
)
from utils.helpers import is_admin, format_anime_caption

router = Router(name="navigation")

PER_PAGE = 10


@router.message(F.text == "🎬 Animalar")
async def show_anime_list(message: Message):
    await render_anime_list(message, page=1, user_id=message.from_user.id)


@router.message(F.text == "🔍 Qidirish")
async def ask_search_query(message: Message, state: FSMContext):
    await message.answer("🔍 Qidirmoqchi bo'lgan anime nomini yozing:")
    from utils.states import AnimeStates
    # Foydalanish uchun alohida oddiy holatdan foydalanamiz
    await state.set_state("waiting_search_query")


@router.message(F.text == "❌ Bekor qilish")
async def cancel_any(message: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        return
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())


@router.message(F.text, lambda m: True)
async def maybe_search_handler(message: Message, state: FSMContext):
    """Qidiruv so'rovini ushlaymiz (faqat shu state bo'lsa)."""
    current_state = await state.get_state()
    if current_state != "waiting_search_query":
        return
    await state.clear()
    query = message.text.strip()

    import aiosqlite
    from config import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        is_adm = is_admin(message.from_user.id)
        sql = "SELECT * FROM animes WHERE title LIKE ? OR fanadub_name LIKE ?"
        if not is_adm:
            sql += " AND is_restricted = 0"
        async with db.execute(sql, (f"%{query}%", f"%{query}%")) as cursor:
            rows = await cursor.fetchall()
            results = [dict(r) for r in rows]

    if not results:
        await message.answer("😔 Hech narsa topilmadi.", reply_markup=main_menu_kb())
        return

    kb = anime_list_kb(results, page=1, total=len(results), per_page=len(results) or 1)
    await message.answer(f"🔍 Topildi: <b>{len(results)}</b> ta natija", reply_markup=kb)


async def render_anime_list(target, page: int, user_id: int, edit: bool = False):
    is_adm = is_admin(user_id)
    total = await get_animes_count(include_restricted=is_adm)
    animes = await get_all_animes(page=page, per_page=PER_PAGE, restricted_for_admin=is_adm)

    if not animes and page == 1:
        text = "😔 Hozircha animalar mavjud emas."
        if edit:
            await target.message.edit_text(text)
        else:
            await target.answer(text)
        return

    kb = anime_list_kb(animes, page=page, total=total, per_page=PER_PAGE)
    text = f"🎬 <b>Animalar ro'yxati</b> (jami: {total})"

    if edit:
        try:
            await target.message.edit_text(text, reply_markup=kb)
        except Exception:
            await target.message.answer(text, reply_markup=kb)
    else:
        await target.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("anime_list:"))
async def cb_anime_list(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await callback.answer()
    await render_anime_list(callback, page=page, user_id=callback.from_user.id, edit=True)


@router.callback_query(F.data.startswith("anime_view:"))
async def cb_anime_view(callback: CallbackQuery):
    anime_id = int(callback.data.split(":")[1])
    anime = await get_anime(anime_id)
    if not anime:
        await callback.answer("Anime topilmadi!", show_alert=True)
        return

    if anime.get("is_restricted") and not is_admin(callback.from_user.id):
        await callback.answer("🔒 Bu anime hozircha mavjud emas.", show_alert=True)
        return

    await callback.answer()
    caption = format_anime_caption(anime)
    kb = anime_view_kb(anime_id, is_admin=is_admin(callback.from_user.id))

    try:
        await callback.message.delete()
    except Exception:
        pass

    if anime.get("poster_file_id"):
        await callback.message.answer_photo(
            photo=anime["poster_file_id"], caption=caption, reply_markup=kb
        )
    else:
        await callback.message.answer(caption, reply_markup=kb)


@router.callback_query(F.data.startswith("episodes:"))
async def cb_episodes(callback: CallbackQuery):
    parts = callback.data.split(":")
    anime_id, page = int(parts[1]), int(parts[2])
    episodes = await get_episodes(anime_id)

    if not episodes:
        await callback.answer("📭 Hozircha epizodlar yo'q.", show_alert=True)
        return

    await callback.answer()
    kb = episodes_kb(episodes, anime_id, page=page)
    text = f"📺 <b>Epizodlar</b> (jami: {len(episodes)})"

    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("episode_play:"))
async def cb_episode_play(callback: CallbackQuery):
    episode_id = int(callback.data.split(":")[1])
    episode = await get_episode(episode_id)
    if not episode:
        await callback.answer("Epizod topilmadi!", show_alert=True)
        return

    anime = await get_anime(episode["anime_id"])
    if anime.get("is_restricted") and not is_admin(callback.from_user.id):
        await callback.answer("🔒 Bu anime hozircha mavjud emas.", show_alert=True)
        return

    await callback.answer()
    episodes = await get_episodes(episode["anime_id"])
    kb = episode_nav_kb(episodes, episode_id, episode["anime_id"])

    caption = f"🎬 <b>{anime['title']}</b>\n📺 {episode['episode_number']}-qism"
    if episode.get("title"):
        caption += f" - {episode['title']}"

    try:
        await callback.message.delete()
    except Exception:
        pass

    if episode.get("video_file_id"):
        await callback.message.answer_video(
            video=episode["video_file_id"],
            caption=caption,
            reply_markup=kb
        )
    else:
        await callback.message.answer(
            caption + "\n\n⚠️ Video hali yuklanmagan.", reply_markup=kb
        )


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("🏠 Bosh sahifa", reply_markup=main_menu_kb())


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    await callback.answer()
