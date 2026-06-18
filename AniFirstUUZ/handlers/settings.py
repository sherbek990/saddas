from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database.db import get_all_settings, set_setting, get_setting
from keyboards.main_kb import admin_settings_kb, admin_main_kb, cancel_kb
from utils.helpers import is_admin
from utils.states import SettingStates

router = Router(name="settings")


@router.callback_query(F.data == "admin_settings")
async def cb_admin_settings(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
    await callback.answer()
    settings = await get_all_settings()
    text = "⚙️ <b>Birlamchi Sozlamalar</b>\n\nKerakli sozlamani tanlang:"
    await callback.message.edit_text(text, reply_markup=admin_settings_kb(settings))


@router.callback_query(F.data.startswith("setting_toggle:"))
async def cb_setting_toggle(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)

    key = callback.data.split(":")[1]
    current = await get_setting(key, "0")
    new_value = "0" if current == "1" else "1"
    await set_setting(key, new_value)

    await callback.answer("✅ Sozlama yangilandi!")
    settings = await get_all_settings()
    await callback.message.edit_reply_markup(reply_markup=admin_settings_kb(settings))


@router.callback_query(F.data.startswith("setting_edit:"))
async def cb_setting_edit_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)

    key = callback.data.split(":")[1]
    await state.update_data(setting_key=key)
    await state.set_state(SettingStates.waiting_value)
    await callback.answer()

    labels = {"welcome_text": "Xush kelibsiz matni", "bot_name": "Bot nomi"}
    current_value = await get_setting(key, "")
    await callback.message.answer(
        f"📝 <b>{labels.get(key, key)}</b> uchun yangi qiymat kiriting:\n\n"
        f"Hozirgi qiymat:\n<code>{current_value}</code>",
        reply_markup=cancel_kb()
    )


@router.message(SettingStates.waiting_value)
async def setting_value_received(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())

    data = await state.get_data()
    key = data["setting_key"]
    await set_setting(key, message.html_text or message.text)
    await state.clear()

    await message.answer("✅ Sozlama muvaffaqiyatli yangilandi!", reply_markup=admin_main_kb())
