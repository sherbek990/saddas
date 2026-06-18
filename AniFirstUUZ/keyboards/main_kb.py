from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


# ==================== USER KEYBOARDS ====================

def main_menu_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🎬 Animalar"),
        KeyboardButton(text="🔍 Qidirish")
    )
    builder.row(
        KeyboardButton(text="⚙️ Sozlamalar"),
        KeyboardButton(text="📊 Statistika")
    )
    return builder.as_markup(resize_keyboard=True)


def anime_list_kb(animes: list, page: int, total: int, per_page: int = 10):
    builder = InlineKeyboardBuilder()
    for anime in animes:
        restricted = "🔒 " if anime.get("is_restricted") else ""
        builder.row(InlineKeyboardButton(
            text=f"{restricted}{anime['title']}",
            callback_data=f"anime_view:{anime['id']}"
        ))

    # Pagination
    nav_buttons = []
    total_pages = (total + per_page - 1) // per_page
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldin", callback_data=f"anime_list:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"anime_list:{page+1}"))

    if nav_buttons:
        builder.row(*nav_buttons)

    return builder.as_markup()


def anime_view_kb(anime_id: int, is_admin: bool = False):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="📺 Epizodlar", callback_data=f"episodes:{anime_id}:1"
    ))
    if is_admin:
        builder.row(
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"anime_edit:{anime_id}"),
            InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"anime_delete:{anime_id}")
        )
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="anime_list:1"))
    return builder.as_markup()


def episodes_kb(episodes: list, anime_id: int, page: int = 1, per_page: int = 10):
    builder = InlineKeyboardBuilder()
    start_idx = (page - 1) * per_page
    page_episodes = episodes[start_idx:start_idx + per_page]

    for ep in page_episodes:
        builder.row(InlineKeyboardButton(
            text=f"📹 {ep['episode_number']}-qism{' - ' + ep['title'] if ep.get('title') else ''}",
            callback_data=f"episode_play:{ep['id']}"
        ))

    # Navigation
    total_pages = (len(episodes) + per_page - 1) // per_page
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"episodes:{anime_id}:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"episodes:{anime_id}:{page+1}"))
    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"anime_view:{anime_id}"))
    return builder.as_markup()


def episode_nav_kb(episodes: list, current_ep_id: int, anime_id: int):
    """Epizod ko'rishda oldin/keyingi navigatsiya"""
    builder = InlineKeyboardBuilder()
    ids = [ep["id"] for ep in episodes]
    idx = ids.index(current_ep_id) if current_ep_id in ids else -1

    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton(
            text="⬅️ Oldingi", callback_data=f"episode_play:{ids[idx-1]}"
        ))
    if idx < len(ids) - 1:
        nav.append(InlineKeyboardButton(
            text="Keyingi ➡️", callback_data=f"episode_play:{ids[idx+1]}"
        ))
    if nav:
        builder.row(*nav)

    builder.row(
        InlineKeyboardButton(text="📋 Barcha qismlar", callback_data=f"episodes:{anime_id}:1"),
        InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="main_menu")
    )
    return builder.as_markup()


def subscription_check_kb(channels: list):
    builder = InlineKeyboardBuilder()
    for ch in channels:
        emoji = {"telegram": "📢", "instagram": "📸", "youtube": "▶️"}.get(ch["platform"], "🔗")
        builder.row(InlineKeyboardButton(
            text=f"{emoji} {ch['channel_name']}",
            url=ch["channel_link"]
        ))
    builder.row(InlineKeyboardButton(
        text="✅ Tekshirish", callback_data="check_subscription"
    ))
    return builder.as_markup()


# ==================== ADMIN KEYBOARDS ====================

def admin_main_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎬 Anime boshqaruv", callback_data="admin_animes"),
        InlineKeyboardButton(text="📤 Post yuborish", callback_data="admin_post")
    )
    builder.row(
        InlineKeyboardButton(text="🔗 Obuna kanallari", callback_data="admin_channels"),
        InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="admin_settings")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
        InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users")
    )
    builder.row(
        InlineKeyboardButton(text="📡 Kanallar (Post)", callback_data="admin_broadcast_channels")
    )
    return builder.as_markup()


def admin_anime_list_kb(animes: list, page: int, total: int, per_page: int = 8):
    builder = InlineKeyboardBuilder()
    for anime in animes:
        status = "🔒" if anime.get("is_restricted") else "✅"
        builder.row(InlineKeyboardButton(
            text=f"{status} {anime['title']}",
            callback_data=f"admin_anime_detail:{anime['id']}"
        ))

    total_pages = max(1, (total + per_page - 1) // per_page)
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_animes_page:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_animes_page:{page+1}"))
    if nav:
        builder.row(*nav)

    builder.row(
        InlineKeyboardButton(text="➕ Yangi anime", callback_data="admin_anime_add"),
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")
    )
    return builder.as_markup()


def admin_anime_detail_kb(anime_id: int, is_restricted: bool):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"admin_anime_edit:{anime_id}"),
        InlineKeyboardButton(text="📹 Video qo'shish", callback_data=f"admin_episode_add:{anime_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Epizodlar", callback_data=f"admin_episodes:{anime_id}"),
        InlineKeyboardButton(
            text="🔓 Ruxsat berish" if is_restricted else "🔒 Cheklash",
            callback_data=f"admin_anime_restrict:{anime_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"admin_anime_delete_confirm:{anime_id}"),
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_animes")
    )
    return builder.as_markup()


def admin_anime_edit_kb(anime_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Nomi", callback_data=f"anime_edit_field:{anime_id}:title"),
        InlineKeyboardButton(text="🎌 Fanadub nomi", callback_data=f"anime_edit_field:{anime_id}:fanadub_name")
    )
    builder.row(
        InlineKeyboardButton(text="📄 Tavsif", callback_data=f"anime_edit_field:{anime_id}:description"),
        InlineKeyboardButton(text="🏷️ Janr", callback_data=f"anime_edit_field:{anime_id}:genre")
    )
    builder.row(
        InlineKeyboardButton(text="🖼️ Poster", callback_data=f"anime_edit_field:{anime_id}:poster"),
        InlineKeyboardButton(text="📊 Status", callback_data=f"anime_edit_field:{anime_id}:status")
    )
    builder.row(InlineKeyboardButton(
        text="🔙 Orqaga", callback_data=f"admin_anime_detail:{anime_id}"
    ))
    return builder.as_markup()


def admin_episode_list_kb(episodes: list, anime_id: int):
    builder = InlineKeyboardBuilder()
    for ep in episodes:
        builder.row(InlineKeyboardButton(
            text=f"✏️ {ep['episode_number']}-qism",
            callback_data=f"admin_episode_edit:{ep['id']}"
        ))
    builder.row(
        InlineKeyboardButton(text="➕ Qo'shish", callback_data=f"admin_episode_add:{anime_id}"),
        InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"admin_anime_detail:{anime_id}")
    )
    return builder.as_markup()


def admin_episode_edit_kb(episode_id: int, anime_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎬 Video almashtiruv", callback_data=f"ep_edit_video:{episode_id}"),
        InlineKeyboardButton(text="🖼️ Thumbnail", callback_data=f"ep_edit_thumb:{episode_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📝 Sarlavha", callback_data=f"ep_edit_title:{episode_id}"),
        InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"ep_delete_confirm:{episode_id}")
    )
    builder.row(InlineKeyboardButton(
        text="🔙 Orqaga", callback_data=f"admin_episodes:{anime_id}"
    ))
    return builder.as_markup()


def admin_channels_kb(channels: list):
    builder = InlineKeyboardBuilder()
    for ch in channels:
        status = "✅" if ch["is_active"] else "❌"
        emoji = {"telegram": "📢", "instagram": "📸", "youtube": "▶️"}.get(ch["platform"], "🔗")
        builder.row(InlineKeyboardButton(
            text=f"{status} {emoji} {ch['channel_name']}",
            callback_data=f"channel_toggle:{ch['id']}"
        ))
    builder.row(
        InlineKeyboardButton(text="➕ Telegram", callback_data="add_channel:telegram"),
        InlineKeyboardButton(text="➕ Instagram", callback_data="add_channel:instagram"),
        InlineKeyboardButton(text="➕ YouTube", callback_data="add_channel:youtube")
    )
    builder.row(InlineKeyboardButton(text="🗑️ O'chirish", callback_data="delete_channel_select"))
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel"))
    return builder.as_markup()


def admin_post_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Matn yuborish", callback_data="post_text"),
        InlineKeyboardButton(text="🖼️ Rasm + Matn", callback_data="post_photo")
    )
    builder.row(
        InlineKeyboardButton(text="🎬 Video + Matn", callback_data="post_video"),
        InlineKeyboardButton(text="📢 Hammaga xabar", callback_data="broadcast_all")
    )
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel"))
    return builder.as_markup()


def post_anime_select_kb(animes: list, page: int, total: int, per_page: int = 8):
    """Postni qaysi animega bog'lashni tanlash uchun klaviatura
    (Tomosha qilish tugmasi shu anime'ga deep link bo'ladi)."""
    builder = InlineKeyboardBuilder()
    for anime in animes:
        builder.row(InlineKeyboardButton(
            text=f"🎬 {anime['title']}",
            callback_data=f"post_select_anime:{anime['id']}"
        ))

    total_pages = max(1, (total + per_page - 1) // per_page)
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"post_anime_page:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"post_anime_page:{page+1}"))
    if nav:
        builder.row(*nav)

    builder.row(InlineKeyboardButton(text="🚫 Havolasiz yuborish", callback_data="post_no_anime"))
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_post"))
    return builder.as_markup()


def admin_settings_kb(settings: dict):
    sub_req = "✅" if settings.get("subscription_required") == "1" else "❌"
    maintenance = "✅" if settings.get("maintenance_mode") == "1" else "❌"
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"{sub_req} Majburiy obuna",
            callback_data="setting_toggle:subscription_required"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{maintenance} Texnik ishlar rejimi",
            callback_data="setting_toggle:maintenance_mode"
        )
    )
    builder.row(
        InlineKeyboardButton(text="📝 Xush kelibsiz matni", callback_data="setting_edit:welcome_text"),
        InlineKeyboardButton(text="🤖 Bot nomi", callback_data="setting_edit:bot_name")
    )
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel"))
    return builder.as_markup()


def confirm_kb(action: str, item_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"confirm_{action}:{item_id}"),
        InlineKeyboardButton(text="❌ Yo'q", callback_data=f"cancel_{action}:{item_id}")
    )
    return builder.as_markup()


def back_kb(callback: str):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data=callback))
    return builder.as_markup()


def cancel_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)
