from config import ADMIN_IDS, SUPER_ADMIN_ID


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS or user_id == SUPER_ADMIN_ID


def is_super_admin(user_id: int) -> bool:
    return user_id == SUPER_ADMIN_ID


def format_anime_caption(anime: dict) -> str:
    text = f"🎬 <b>{anime['title']}</b>\n"
    if anime.get("fanadub_name"):
        text += f"🎌 Fandub: {anime['fanadub_name']}\n"
    if anime.get("genre"):
        text += f"🏷️ Janr: {anime['genre']}\n"
    status_map = {"ongoing": "🟢 Davom etmoqda", "completed": "✅ Yakunlangan"}
    text += f"📊 Status: {status_map.get(anime.get('status'), anime.get('status', '-'))}\n"
    if anime.get("description"):
        text += f"\n📄 {anime['description']}\n"
    return text


def chunk_list(lst: list, n: int):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
