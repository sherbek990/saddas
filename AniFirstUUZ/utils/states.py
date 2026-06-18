from aiogram.fsm.state import State, StatesGroup


class AnimeStates(StatesGroup):
    waiting_title = State()
    waiting_fanadub_name = State()
    waiting_description = State()
    waiting_genre = State()
    waiting_poster = State()
    confirm = State()


class AnimeEditStates(StatesGroup):
    waiting_value = State()


class EpisodeStates(StatesGroup):
    waiting_number = State()
    waiting_title = State()
    waiting_video = State()
    waiting_thumbnail = State()


class EpisodeEditStates(StatesGroup):
    waiting_video = State()
    waiting_thumbnail = State()
    waiting_title = State()


class ChannelStates(StatesGroup):
    waiting_name = State()
    waiting_link = State()
    waiting_id = State()


class PostStates(StatesGroup):
    waiting_anime_choice = State()
    waiting_text = State()
    waiting_photo = State()
    waiting_video = State()
    waiting_channels = State()
    waiting_broadcast_text = State()


class SettingStates(StatesGroup):
    waiting_value = State()
