#any problems dm at telegram @franited
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import pyromod  # required for message.chat.ask

# 1) Configuration
API_ID = int(os.environ.get("API_ID", "")) # your api id over here 
API_HASH = os.environ.get("API_HASH", "") # your api hash over here
BOT_TOKEN = os.environ.get("BOT_TOKEN", "") #your bot token over here
OWNER_ID = int(os.environ.get("OWNER_ID", "")) #your owner id over here
STRING_SESSION = os.environ.get("STRING_SESSION", "").strip() #your string session over here

ALLOWED_USERS = [OWNER_ID] # you can add a comma and add your freinds id so his use

LOG_CHANNEL_1 = "" # log channel id/usernme . where all your logs will be stored ... exmple @mylogsbro
LOG_CHANNEL_2 =  # your main channel where thr stuff will go from getting cloned .. exmaple -1001522123008

CUSTOM_CAPTION = "" # if you want add a custom caption else leave it ""
CLONE_DELAY = 30 # the delay how much delay you want in each file but keep it 30 for no interfaernce from telegram

# 2) Per-user settings
default_owner_settings = {"log1": True, "log2": True, "dm": False}
default_user_settings = {"log1": True, "log2": False, "dm": True}

ALL_FILTER_TYPES = ["video", "photo", "document", "audio", "voice", "gif", "sticker", "text"]
FILTER_LABELS = {
    "video": "Videos",
    "photo": "Photos",
    "document": "Files/Docs",
    "audio": "Audio",
    "voice": "Voice Notes",
    "gif": "GIFs",
    "sticker": "Stickers",
    "text": "Text Messages",
}

user_settings = {}
user_filters = {}
cancel_flags = {}


def get_user_settings(user_id: int):
    if user_id not in user_settings:
        if user_id == OWNER_ID:
            user_settings[user_id] = dict(default_owner_settings)
        else:
            user_settings[user_id] = dict(default_user_settings)
    return user_settings[user_id]


def get_user_filters(user_id: int):
    if user_id not in user_filters:
        user_filters[user_id] = {k: True for k in ALL_FILTER_TYPES}
    return user_filters[user_id]


def get_destinations(user_id: int):
    s = get_user_settings(user_id)
    destinations = []
    if s.get("log1"):
        destinations.append(("log1", LOG_CHANNEL_1))
    if s.get("log2"):
        destinations.append(("log2", LOG_CHANNEL_2))
    if s.get("dm"):
        destinations.append(("dm", user_id))
    return destinations


def is_type_allowed(user_id: int, msg):
    f = get_user_filters(user_id)
    if msg.animation:
        return f.get("gif", True)
    if msg.video:
        return f.get("video", True)
    if msg.photo:
        return f.get("photo", True)
    if msg.audio:
        return f.get("audio", True)
    if msg.voice:
        return f.get("voice", True)
    if msg.document:
        return f.get("document", True)
    if msg.sticker:
        return f.get("sticker", True)
    if msg.text:
        return f.get("text", True)
    return True


def sanitize_link_token(link: str):
    s = (link or "").strip()
    for marker in ("?single", "&single"):
        if s.lower().endswith(marker):
            s = s[: -len(marker)]
            break
    return s.rstrip("/")


def get_link_data(link: str):
    if not link:
        return None, None, False
    link = sanitize_link_token(link)
    try:
        if "t.me/c/" in link:
            parts = link.split("t.me/c/")[1].split("/")
            return int("-100" + parts[0]), int(parts[1]), True
        if "t.me/b/" in link:
            parts = link.split("t.me/b/")[1].split("/")
            return parts[0], int(parts[1]), True
        if "t.me/" in link:
            parts = link.split("t.me/")[1].split("/")
            return parts[0], int(parts[1]), False
    except Exception:
        return None, None, False
    return None, None, False


def parse_start_input(text: str):
    raw = (text or "").strip()
    parts = raw.split()
    if not parts:
        return None, False, False
    link = parts[0]
    single_mode = link.lower().endswith(("?single", "&single"))
    rename_mode = any(p.lower() in {"-r", "-rename"} for p in parts[1:])
    return link, rename_mode, single_mode


def get_media_filename(msg, fallback_msg_id: int):
    if msg.document and msg.document.file_name:
        return msg.document.file_name
    if msg.video and msg.video.file_name:
        return msg.video.file_name
    if msg.audio and msg.audio.file_name:
        return msg.audio.file_name
    if msg.voice:
        return f"voice_{fallback_msg_id}.ogg"
    if msg.photo:
        return f"photo_{fallback_msg_id}.jpg"
    if msg.animation:
        return f"gif_{fallback_msg_id}.mp4"
    if msg.sticker:
        ext = ".webp"
        if getattr(msg.sticker, "is_video", False):
            ext = ".webm"
        return f"sticker_{fallback_msg_id}{ext}"
    return f"file_{fallback_msg_id}"


def build_settings_text(user_id: int):
    s = get_user_settings(user_id)
    is_owner = user_id == OWNER_ID

    def status(k):
        return "Enabled" if s.get(k) else "Disabled"

    lines = ["**Settings - Delivery Options**", ""]
    lines.append("- Log Channel 1: Always On (locked)")
    lines.append(f"- Log Channel 2: {status('log2') if is_owner else 'Disabled (owner-only)'}")
    lines.append(f"- DM by Bot: {status('dm')}")
    lines.append("")
    lines.append("Tap a button to toggle.")
    return "\n".join(lines)


def build_settings_keyboard(user_id: int):
    s = get_user_settings(user_id)
    is_owner = user_id == OWNER_ID

    def btn(label, key):
        icon = "[ON]" if s.get(key, False) else "[OFF]"
        return InlineKeyboardButton(f"{icon} {label}", callback_data=f"stg_{key}_{user_id}")

    rows = [[InlineKeyboardButton("[ON] Log Channel 1 (Always On)", callback_data="log1_locked")]]

    if is_owner:
        rows.append([btn("Log Channel 2", "log2")])
    else:
        rows.append([InlineKeyboardButton("[OFF] Log Channel 2 (Owner-only)", callback_data="log2_locked")])

    rows.append([btn("DM by Bot", "dm")])
    rows.append([InlineKeyboardButton("Filter", callback_data=f"open_filter_{user_id}")])
    rows.append([InlineKeyboardButton("Close", callback_data="close_settings")])
    return InlineKeyboardMarkup(rows)


def build_filter_text(user_id: int):
    f = get_user_filters(user_id)
    active = sum(1 for v in f.values() if v)
    lines = ["**Filter Settings**", "Only selected types will be cloned.", ""]
    for key in ALL_FILTER_TYPES:
        icon = "[ON]" if f.get(key, True) else "[OFF]"
        lines.append(f"{icon} {FILTER_LABELS[key]}")
    lines.append("")
    lines.append(f"Active: {active}/{len(ALL_FILTER_TYPES)}")
    return "\n".join(lines)


def build_filter_keyboard(user_id: int):
    f = get_user_filters(user_id)
    rows = []
    for ftype in ALL_FILTER_TYPES:
        icon = "[ON]" if f.get(ftype, True) else "[OFF]"
        rows.append([InlineKeyboardButton(f"{icon} {FILTER_LABELS[ftype]}", callback_data=f"ftog_{ftype}_{user_id}")])
    rows.append([
        InlineKeyboardButton("[ON] All", callback_data=f"fall_on_{user_id}"),
        InlineKeyboardButton("[OFF] None", callback_data=f"fall_off_{user_id}"),
    ])
    rows.append([InlineKeyboardButton("Back to Settings", callback_data=f"back_settings_{user_id}")])
    return InlineKeyboardMarkup(rows)


def cancel_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Cancel", callback_data="cancel_clone")]])


async def ensure_user_connected():
    if not user.is_connected:
        await user.start()




def readable_size(size: int | float | None):
    if not size:
        return "0B"
    size = float(size)
    units = ["B", "KB", "MB", "GB", "TB"]
    idx = 0
    while size >= 1024 and idx < len(units) - 1:
        size /= 1024
        idx += 1
    if idx == 0:
        return f"{int(size)}B"
    return f"{size:.2f}{units[idx]}"


def readable_time(seconds: int | float | None):
    if not seconds or seconds < 0:
        return "-"
    seconds = int(seconds)
    parts = []
    for name, value in (("d", 86400), ("h", 3600), ("m", 60), ("s", 1)):
        if seconds >= value:
            amount, seconds = divmod(seconds, value)
            parts.append(f"{amount}{name}")
    return " ".join(parts[:3]) or "0s"


def progress_bar(percent: float):
    percent = max(0.0, min(100.0, percent))
    filled = int(percent / 100 * 12)
    return "\u2b22" * filled + "\u2b21" * (12 - filled)


def get_media_size(msg):
    for media in (msg.document, msg.video, msg.audio, msg.voice, msg.animation, msg.sticker, msg.photo):
        if media and getattr(media, "file_size", None):
            return media.file_size
    return 0


def build_progress_text(filename: str, task_by: str, current: int, total: int, status: str, speed: float, eta: str):
    total = total or 0
    percent = (current / total * 100) if total else 0
    return (
        f"{filename}\n\n"
        f"Task By:{task_by}\n"
        f"\u251f [{progress_bar(percent)}] {percent:.1f}%\n"
        f"\u2520 Processed \u2192 {readable_size(current)} of {readable_size(total)}\n"
        f"\u2520 Status \u2192 {status}\n"
        f"\u2520 Speed \u2192 {readable_size(speed)}/s\n"
        f"\u2520 ETA \u2192 - {eta}"
    )


class ProgressTracker:
    def __init__(self, status_msg, filename: str, task_by: str, status: str):
        self.status_msg = status_msg
        self.filename = filename
        self.task_by = task_by
        self.status = status
        self.start = asyncio.get_event_loop().time()
        self.last_edit = 0

    async def update(self, current: int, total: int, force: bool = False):
        if not self.status_msg:
            return
        now = asyncio.get_event_loop().time()
        if not force and now - self.last_edit < 2:
            return
        self.last_edit = now
        elapsed = max(now - self.start, 0.001)
        speed = current / elapsed
        eta = readable_time((total - current) / speed) if total and speed > 0 else "-"
        try:
            await self.status_msg.edit_text(
                build_progress_text(self.filename, self.task_by, current, total, self.status, speed, eta),
                reply_markup=cancel_button(),
            )
        except Exception:
            pass


async def progress_callback(current, total, tracker: ProgressTracker):
    await tracker.update(current, total, force=current >= total)


async def show_transfer_status(status_msg, filename: str, task_by: str, status: str, current: int = 0, total: int = 0):
    if not status_msg:
        return
    try:
        await status_msg.edit_text(
            build_progress_text(filename, task_by, current, total, status, 0, "-"),
            reply_markup=cancel_button(),
        )
    except Exception:
        pass


def clean_upload_name(name: str):
    name = os.path.basename((name or "").strip())
    for ch in '<>:"/\\|?*':
        name = name.replace(ch, "_")
    return name or "renamed_file"


def rename_local_file(local_path: str, new_name: str):
    target = os.path.join(os.path.dirname(local_path), clean_upload_name(new_name))
    if os.path.abspath(target) != os.path.abspath(local_path):
        if os.path.exists(target):
            os.remove(target)
        os.replace(local_path, target)
    return target

def get_message_type(msg):
    if msg.document:
        return "document"
    if msg.video:
        return "video"
    if msg.animation:
        return "animation"
    if msg.sticker:
        return "sticker"
    if msg.voice:
        return "voice"
    if msg.audio:
        return "audio"
    if msg.photo:
        return "photo"
    if msg.text:
        return "text"
    return None


async def send_downloaded_file(dest_id: int, msg, local_path: str, caption: str, rename_to: str | None = None, sender=None, progress_tracker=None):
    sender = sender or bot
    # Renamed files are uploaded as documents so Telegram keeps the requested filename.
    if rename_to:
        return await sender.send_document(dest_id, local_path, caption=caption, progress=progress_callback if progress_tracker else None, progress_args=(progress_tracker,) if progress_tracker else ())

    msg_type = get_message_type(msg)
    caption_to_send = None if msg_type == "sticker" else caption

    if msg_type == "photo":
        return await sender.send_photo(dest_id, local_path, caption=caption_to_send, progress=progress_callback if progress_tracker else None, progress_args=(progress_tracker,) if progress_tracker else ())
    elif msg_type == "video":
        return await sender.send_video(
            dest_id,
            local_path,
            caption=caption_to_send,
            duration=getattr(msg.video, "duration", None),
            width=getattr(msg.video, "width", None),
            height=getattr(msg.video, "height", None),
            progress=progress_callback if progress_tracker else None,
            progress_args=(progress_tracker,) if progress_tracker else (),
        )
    elif msg_type == "audio":
        return await sender.send_audio(dest_id, local_path, caption=caption_to_send, progress=progress_callback if progress_tracker else None, progress_args=(progress_tracker,) if progress_tracker else ())
    elif msg_type == "voice":
        return await sender.send_voice(dest_id, local_path, caption=caption_to_send, progress=progress_callback if progress_tracker else None, progress_args=(progress_tracker,) if progress_tracker else ())
    elif msg_type == "animation":
        return await sender.send_animation(dest_id, local_path, caption=caption_to_send, progress=progress_callback if progress_tracker else None, progress_args=(progress_tracker,) if progress_tracker else ())
    elif msg_type == "sticker":
        return await sender.send_sticker(dest_id, local_path, progress=progress_callback if progress_tracker else None, progress_args=(progress_tracker,) if progress_tracker else ())
    else:
        return await sender.send_document(dest_id, local_path, caption=caption_to_send, progress=progress_callback if progress_tracker else None, progress_args=(progress_tracker,) if progress_tracker else ())


async def download_and_upload_message(source_client, msg, msg_id: int, destinations, rename_to: str | None = None, status_msg=None, task_by: str = "Unknown"):
    if msg.text and not msg.media:
        sent_count = 0
        base_chat_id = None
        base_msg_id = None
        pending_dm_ids = []
        for dest_key, dest_id in destinations:
            if dest_key == "dm":
                pending_dm_ids.append(dest_id)
                continue
            try:
                sent = await bot.send_message(dest_id, f"{msg.text}\n\n{CUSTOM_CAPTION}")
                sent_count += 1
                if dest_key == "log1" and base_chat_id is None:
                    base_chat_id = dest_id
                    base_msg_id = sent.id
            except Exception as e:
                print(f"Failed to send text to {dest_key} ({dest_id}) with bot: {e}")
                if dest_key.startswith("log"):
                    try:
                        await ensure_user_connected()
                        sent = await user.send_message(dest_id, f"{msg.text}\n\n{CUSTOM_CAPTION}")
                        sent_count += 1
                        if dest_key == "log1" and base_chat_id is None:
                            base_chat_id = dest_id
                            base_msg_id = sent.id
                    except Exception as user_error:
                        print(f"Failed to send text to {dest_key} ({dest_id}) with user: {user_error}")
        if base_chat_id and base_msg_id:
            for dm_id in pending_dm_ids:
                await bot.forward_messages(dm_id, base_chat_id, base_msg_id)
                sent_count += 1
        return ("success", "Text sent") if sent_count else ("failed", "Could not send text")

    base_name = rename_to if rename_to else get_media_filename(msg, msg_id)
    total_size = get_media_size(msg)
    dl_tracker = ProgressTracker(status_msg, base_name, task_by, "Download") if status_msg else None
    try:
        if dl_tracker:
            await dl_tracker.update(0, total_size, force=True)
        # Save-restricted bots use the user/source client for protected/private media.
        file_path = await source_client.download_media(
            msg,
            file_name=clean_upload_name(base_name),
            progress=progress_callback if dl_tracker else None,
            progress_args=(dl_tracker,) if dl_tracker else (),
        )
    except Exception as e:
        print(f"Source client download failed for msg {msg_id}: {e}")
        return "failed", f"Download failed: {e}"
    if dl_tracker:
        await dl_tracker.update(total_size or (os.path.getsize(file_path) if file_path and os.path.exists(file_path) else 0), total_size or (os.path.getsize(file_path) if file_path and os.path.exists(file_path) else 0), force=True)
    if not file_path:
        return "failed", "Could not download media"

    try:
        if rename_to:
            file_path = rename_local_file(file_path, rename_to)
        base_name = rename_to if rename_to else get_media_filename(msg, msg_id)
        caption = f"**{base_name}**\n\n{CUSTOM_CAPTION}"
        sent_count = 0
        base_chat_id = None
        base_msg_id = None
        pending_dm_ids = []
        for dest_key, dest_id in destinations:
            if dest_key == "dm":
                pending_dm_ids.append(dest_id)
                continue
            try:
                up_tracker = ProgressTracker(status_msg, base_name, task_by, "Upload") if status_msg and dest_key == "log1" else None
                if up_tracker:
                    await up_tracker.update(0, os.path.getsize(file_path), force=True)
                sent = await send_downloaded_file(dest_id, msg, file_path, caption, rename_to=rename_to, progress_tracker=up_tracker)
                sent_count += 1
                if dest_key == "log1" and base_chat_id is None:
                    base_chat_id = dest_id
                    base_msg_id = sent.id
            except Exception as e:
                print(f"Failed to upload to {dest_key} ({dest_id}) with bot: {e}")
                if dest_key.startswith("log"):
                    try:
                        await ensure_user_connected()
                        up_tracker = ProgressTracker(status_msg, base_name, task_by, "Upload") if status_msg and dest_key == "log1" else None
                        if up_tracker:
                            await up_tracker.update(0, os.path.getsize(file_path), force=True)
                        sent = await send_downloaded_file(dest_id, msg, file_path, caption, rename_to=rename_to, sender=user, progress_tracker=up_tracker)
                        sent_count += 1
                        if dest_key == "log1" and base_chat_id is None:
                            base_chat_id = dest_id
                            base_msg_id = sent.id
                    except Exception as user_error:
                        print(f"Failed to upload to {dest_key} ({dest_id}) with user: {user_error}")
        if base_chat_id and base_msg_id:
            for dm_id in pending_dm_ids:
                await bot.forward_messages(dm_id, base_chat_id, base_msg_id)
                sent_count += 1
        return ("success", "Uploaded") if sent_count else ("failed", "Could not upload")
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)


async def fetch_private_message(src_chat, msg_id: int):
    # Save-restricted style: use the user session directly. Only scan dialogs if
    # Pyrogram has not cached the private peer/access hash yet.
    try:
        return await user.get_messages(src_chat, msg_id)
    except Exception as first_error:
        last_error = first_error

    try:
        async for dialog in user.get_dialogs():
            chat = dialog.chat
            if chat.id == src_chat or getattr(chat, "username", None) == src_chat:
                try:
                    return await user.get_messages(chat.id, msg_id)
                except Exception as retry_error:
                    last_error = retry_error
                    break
    except Exception as dialog_error:
        last_error = dialog_error

    raise RuntimeError(
        "Private source not accessible by STRING_SESSION. "
        "Make sure the string-session account is joined in that private chat/channel. "
        f"Telegram error: {last_error}"
    )


async def get_source_message(src_chat, msg_id: int, is_private: bool, prefer_user: bool = False, status_msg=None, task_by: str = "Unknown"):
    if is_private or prefer_user:
        await ensure_user_connected()
        await show_transfer_status(status_msg, f"message_{msg_id}", task_by, "Resolving")
        if is_private:
            return await fetch_private_message(src_chat, msg_id), user
        return await user.get_messages(src_chat, msg_id), user

    try:
        return await bot.get_messages(src_chat, msg_id), bot
    except Exception:
        await ensure_user_connected()
        return await user.get_messages(src_chat, msg_id), user


async def transfer_single_message(uid: int, src_chat, msg_id: int, is_private: bool, rename_to: str | None = None, status_msg=None, task_by: str = "Unknown"):
    msg, source_client = await get_source_message(src_chat, msg_id, is_private, status_msg=status_msg if is_private else None, task_by=task_by)

    if not msg or getattr(msg, "empty", False):
        return "skipped", "Message not found"
    if not is_type_allowed(uid, msg):
        return "skipped", "Filtered by settings"

    destinations = get_destinations(uid)
    if not destinations:
        return "failed", "No destination enabled"

    if is_private or rename_to:
        try:
            return await download_and_upload_message(source_client, msg, msg_id, destinations, rename_to=rename_to, status_msg=status_msg, task_by=task_by)
        except Exception:
            if is_private:
                raise
            msg, source_client = await get_source_message(src_chat, msg_id, is_private, prefer_user=True, status_msg=status_msg, task_by=task_by)
            return await download_and_upload_message(source_client, msg, msg_id, destinations, rename_to=rename_to, status_msg=status_msg, task_by=task_by)

    # Public messages use fast copy first. If Telegram blocks copy, fall back to user download/upload.
    base_name = get_media_filename(msg, msg_id)
    caption = f"**{base_name}**\n\n{CUSTOM_CAPTION}"
    copy_caption = None if msg.sticker else caption
    forwarded_from_ch = None
    forwarded_msg_id = None
    fallback_destinations = []
    pending_dm_ids = []
    sent_count = 0

    for dest_key, dest_id in destinations:
        if dest_key == "dm":
            pending_dm_ids.append(dest_id)
            continue
        try:
            if msg.text and not msg.media:
                sent = await bot.send_message(dest_id, f"{msg.text}\n\n{CUSTOM_CAPTION}")
                sent_count += 1
                if dest_key == "log1" and forwarded_from_ch is None:
                    forwarded_from_ch = dest_id
                    forwarded_msg_id = sent.id
            else:
                sent = await bot.copy_message(dest_id, src_chat, msg_id, caption=copy_caption)
                sent_count += 1
                if dest_key == "log1" and forwarded_from_ch is None:
                    forwarded_from_ch = dest_id
                    forwarded_msg_id = sent.id
        except Exception as e:
            print(f"Failed to copy to {dest_key} ({dest_id}) with bot: {e}")
            if dest_key.startswith("log"):
                try:
                    result, _ = await download_and_upload_message(
                        source_client,
                        msg,
                        msg_id,
                        [(dest_key, dest_id)],
                        status_msg=status_msg,
                        task_by=task_by
                    )
                    if result == "success":
                        sent_count += 1
                        continue
                except Exception as upload_error:
                    print(f"Failed to upload fallback to {dest_key} ({dest_id}): {upload_error}")
            fallback_destinations.append((dest_key, dest_id))

    if fallback_destinations:
        msg, source_client = await get_source_message(src_chat, msg_id, is_private, prefer_user=True, status_msg=status_msg, task_by=task_by)
        result, detail = await download_and_upload_message(source_client, msg, msg_id, fallback_destinations, status_msg=status_msg, task_by=task_by)
        if result == "success":
            sent_count += 1
        elif sent_count == 0:
            return result, detail

    if forwarded_from_ch and forwarded_msg_id:
        for dm_id in pending_dm_ids:
            await bot.forward_messages(dm_id, forwarded_from_ch, forwarded_msg_id)
            sent_count += 1

    return ("success", "Copied") if sent_count > 0 else ("failed", "No destination accepted the file")

print("Connecting clients...")
bot = Client("bot_runner", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("user_runner", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION, no_updates=True)


@bot.on_message(filters.command("settings") & filters.private)
async def settings_handler(_, message):
    uid = message.from_user.id
    if uid not in ALLOWED_USERS:
        await message.reply("Access denied.")
        return
    await message.reply(build_settings_text(uid), reply_markup=build_settings_keyboard(uid))


@bot.on_callback_query(filters.regex(r"^(stg_(log1|log2|dm)_\d+|log1_locked|log2_locked)$"))
async def toggle_setting(_, callback_query):
    requester_id = callback_query.from_user.id

    if callback_query.data == "log1_locked":
        await callback_query.answer("Log Channel 1 is always ON.", show_alert=True)
        return
    if callback_query.data == "log2_locked":
        await callback_query.answer("Log Channel 2 is owner-only.", show_alert=True)
        return

    _, key, target_uid_s = callback_query.data.split("_", 2)
    target_uid = int(target_uid_s)

    if requester_id != target_uid and requester_id != OWNER_ID:
        await callback_query.answer("Not your settings.", show_alert=True)
        return

    if key == "log1":
        await callback_query.answer("Log Channel 1 is always ON.", show_alert=True)
        return

    if key == "log2" and requester_id != OWNER_ID:
        await callback_query.answer("Log Channel 2 is owner-only.", show_alert=True)
        return

    s = get_user_settings(target_uid)
    s[key] = not s[key]
    await callback_query.answer(f"{key} => {'Enabled' if s[key] else 'Disabled'}")
    await callback_query.message.edit_text(build_settings_text(target_uid), reply_markup=build_settings_keyboard(target_uid))


@bot.on_callback_query(filters.regex("close_settings"))
async def close_settings(_, callback_query):
    await callback_query.message.delete()


@bot.on_callback_query(filters.regex(r"^open_filter_\d+$"))
async def open_filter_menu(_, callback_query):
    uid = callback_query.from_user.id
    target_uid = int(callback_query.data.split("_")[2])
    if uid != target_uid and uid != OWNER_ID:
        await callback_query.answer("Not your settings.", show_alert=True)
        return
    await callback_query.answer()
    await callback_query.message.edit_text(build_filter_text(target_uid), reply_markup=build_filter_keyboard(target_uid))


@bot.on_callback_query(filters.regex(r"^ftog_(video|photo|document|audio|voice|gif|sticker|text)_\d+$"))
async def toggle_filter(_, callback_query):
    uid = callback_query.from_user.id
    _, ftype, target_uid_s = callback_query.data.split("_", 2)
    target_uid = int(target_uid_s)

    if uid != target_uid and uid != OWNER_ID:
        await callback_query.answer("Not your settings.", show_alert=True)
        return

    f = get_user_filters(target_uid)
    f[ftype] = not f[ftype]
    await callback_query.answer(f"{FILTER_LABELS[ftype]} => {'On' if f[ftype] else 'Off'}")
    await callback_query.message.edit_text(build_filter_text(target_uid), reply_markup=build_filter_keyboard(target_uid))


@bot.on_callback_query(filters.regex(r"^fall_(on|off)_\d+$"))
async def filter_all(_, callback_query):
    uid = callback_query.from_user.id
    _, action, target_uid_s = callback_query.data.split("_", 2)
    target_uid = int(target_uid_s)

    if uid != target_uid and uid != OWNER_ID:
        await callback_query.answer("Not your settings.", show_alert=True)
        return

    f = get_user_filters(target_uid)
    for k in ALL_FILTER_TYPES:
        f[k] = action == "on"

    await callback_query.answer("All selected" if action == "on" else "All cleared")
    await callback_query.message.edit_text(build_filter_text(target_uid), reply_markup=build_filter_keyboard(target_uid))


@bot.on_callback_query(filters.regex(r"^back_settings_\d+$"))
async def back_to_settings(_, callback_query):
    uid = callback_query.from_user.id
    target_uid = int(callback_query.data.split("_")[2])
    if uid != target_uid and uid != OWNER_ID:
        await callback_query.answer("Not your settings.", show_alert=True)
        return
    await callback_query.answer()
    await callback_query.message.edit_text(build_settings_text(target_uid), reply_markup=build_settings_keyboard(target_uid))


@bot.on_callback_query(filters.regex("cancel_clone"))
async def on_cancel(_, callback_query):
    uid = callback_query.from_user.id
    if uid not in ALLOWED_USERS:
        await callback_query.answer("Not allowed.", show_alert=True)
        return
    cancel_flags[uid] = True
    await callback_query.answer("Cancelling...", show_alert=True)
    try:
        await callback_query.message.edit_text("Cancel requested. Stopping after current message.", reply_markup=None)
    except Exception:
        pass


@bot.on_message(filters.command("adduser") & filters.private)
async def add_user_cmd(_, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("Access denied.")
        return
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.reply("Usage: /adduser USER_ID")
        return
    new_id = int(parts[1])
    if new_id in ALLOWED_USERS:
        await message.reply(f"User {new_id} is already allowed.")
        return
    ALLOWED_USERS.append(new_id)
    await message.reply(f"User {new_id} added.")


@bot.on_message(filters.command("removeuser") & filters.private)
async def remove_user_cmd(_, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("Access denied.")
        return
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.reply("Usage: /removeuser USER_ID")
        return
    rem_id = int(parts[1])
    if rem_id == OWNER_ID:
        await message.reply("Cannot remove owner.")
        return
    if rem_id not in ALLOWED_USERS:
        await message.reply(f"User {rem_id} is not in allow-list.")
        return
    ALLOWED_USERS.remove(rem_id)
    await message.reply(f"User {rem_id} removed.")


@bot.on_message(filters.command("users") & filters.private)
async def list_users_cmd(_, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("Access denied.")
        return
    lines = ["**Allowed Users**", ""]
    for uid in ALLOWED_USERS:
        suffix = " (Owner)" if uid == OWNER_ID else ""
        lines.append(f"- `{uid}`{suffix}")
    await message.reply("\n".join(lines))


@bot.on_message(filters.command("clone") & filters.private)
async def clone_handler(_, message):
    uid = message.from_user.id
    if uid not in ALLOWED_USERS:
        await message.reply("Access denied.")
        return

    cancel_flags[uid] = False

    destinations = get_destinations(uid)
    if not destinations:
        await message.reply("No destination enabled. Use /settings first.")
        return

    if len(message.command) > 1:
        s_text = " ".join(message.command[1:])
    else:
        try:
            s_msg = await message.chat.ask("Send START message link. For rename use: <link> -r", timeout=90)
            s_text = s_msg.text
        except Exception:
            await message.reply("Timeout. Run /clone again.")
            return

    start_link, rename_mode, single_mode = parse_start_input(s_text)
    src_chat, start_id, is_private = get_link_data(start_link)

    if not src_chat or not start_id:
        await message.reply("Invalid START link.")
        return

    if is_private and not user.is_connected:
        await user.start()

    # Single-file rename flow
    if rename_mode:
        try:
            name_msg = await message.chat.ask("Send new file name (example: movie_01.mp4):", timeout=90)
        except Exception:
            await message.reply("Timeout waiting for file name.")
            return

        new_name = (name_msg.text or "").strip()
        if not new_name:
            await message.reply("Invalid file name.")
            return

        status_msg = await message.reply("Renaming and uploading 1 file...", reply_markup=cancel_button())
        try:
            result, detail = await transfer_single_message(uid, src_chat, start_id, is_private, rename_to=new_name, status_msg=status_msg, task_by=(message.from_user.username or message.from_user.first_name or str(uid)))
            if result == "success":
                await status_msg.edit_text(f"Rename complete.\nFile: `{new_name}`", reply_markup=None)
            elif result == "skipped":
                await status_msg.edit_text(f"Skipped: {detail}", reply_markup=None)
            else:
                await status_msg.edit_text(f"Failed: {detail}", reply_markup=None)
        except Exception as e:
            await status_msg.edit_text(f"Rename failed: {e}", reply_markup=None)
        finally:
            cancel_flags[uid] = False
        return

    # Default multi-message flow
    if single_mode:
        end_id = start_id
    else:
        try:
            e_msg = await message.chat.ask("Send END message link:", timeout=60)
        except Exception:
            await message.reply("Timeout. Run /clone again.")
            return

        _, end_id, _ = get_link_data(e_msg.text)
        if not end_id:
            await message.reply("Invalid END link.")
            return

    if end_id < start_id:
        start_id, end_id = end_id, start_id

    task_by = message.from_user.username or message.from_user.first_name or str(uid)

    total = (end_id - start_id) + 1
    status_msg = await message.reply(
        f"Starting clone...\nRange: `{start_id}` to `{end_id}`\nTotal: {total}",
        reply_markup=cancel_button(),
    )

    success = 0
    failed = 0
    skipped = 0

    for msg_id in range(start_id, end_id + 1):
        if cancel_flags.get(uid):
            await status_msg.edit_text(
                f"Clone cancelled.\nSuccess: {success}\nFailed: {failed}\nSkipped: {skipped}\nStopped at: `{msg_id}`",
                reply_markup=None,
            )
            cancel_flags[uid] = False
            return

        if not is_private:
            await status_msg.edit_text(
                f"Cloning...\nMsg: `{msg_id}`\nDone: {success}/{total}\nFailed: {failed} | Skipped: {skipped}",
                reply_markup=cancel_button(),
            )
        else:
            await show_transfer_status(status_msg, f"message_{msg_id}", task_by, "Resolving")

        try:
            result, _ = await transfer_single_message(uid, src_chat, msg_id, is_private, rename_to=None, status_msg=status_msg if is_private else None, task_by=task_by)
            if result == "success":
                success += 1
            elif result == "skipped":
                skipped += 1
            else:
                failed += 1
        except Exception as e:
            print(f"Clone failed for msg {msg_id}: {e}")
            if is_private:
                await show_transfer_status(status_msg, f"message_{msg_id}", task_by, f"Failed: {e}")
            failed += 1

        if not is_private:
            await status_msg.edit_text(
                f"Done: {success}/{total}\nFailed: {failed} | Skipped: {skipped}\nWaiting {CLONE_DELAY}s...",
                reply_markup=cancel_button(),
            )
        else:
            await show_transfer_status(status_msg, f"message_{msg_id}", task_by, "Waiting")
        await asyncio.sleep(CLONE_DELAY)

    await status_msg.edit_text(
        f"Clone complete.\nTotal: {total}\nSuccess: {success}\nFailed: {failed}\nSkipped: {skipped}",
        reply_markup=None,
    )
    cancel_flags[uid] = False


print("Bot started...")
bot.run()
