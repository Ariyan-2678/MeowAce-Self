import os
import sys
import json
import asyncio
from telethon import TelegramClient, events
from telethon.errors import RPCError

from modules.autocatch import autocatch_command, handle_autocatch_trigger, get_catch_cfg
from modules.automeow import automeow_command, resume_automeow_tasks, get_meow_config, process_schedule_event
from modules.autofish import autofish_command, resume_autofish_tasks, get_fish_cfg
from modules.autofridge import autofridge_command, resume_autofridge_tasks, get_fridge_cfg
from modules.show import show_command, get_show_mode
from modules.sched import sched_command
from modules.alias import alias_command, resolve_alias
from modules.proxy import get_proxy_kwargs

CONFIG_FILE = "config.json"
EXAMPLE_CONFIG_FILE = "config.example.json"

def read_config():
    if not os.path.exists(CONFIG_FILE):
        if os.path.exists(EXAMPLE_CONFIG_FILE):
            with open(EXAMPLE_CONFIG_FILE, 'r', encoding='utf-8') as s_file:
                c_data = s_file.read()
            with open(CONFIG_FILE, 'w', encoding='utf-8') as d_file:
                d_file.write(c_data)
            print(f"[!] '{CONFIG_FILE}' was missing. Created from template.")
        else:
            print(f"[!] Error: Config template '{EXAMPLE_CONFIG_FILE}' missing.")
            sys.exit(1)

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            cfg_json = json.load(f)
            multi = cfg_json.get("multi_session", False)
            if not multi:
                a_id = cfg_json.get("api_id")
                a_hash = cfg_json.get("api_hash")
                if not a_id or a_id == 123456 or not a_hash or a_hash == "YOUR_API_HASH_HERE":
                    print(f"[!] Invalid api_id/api_hash in '{CONFIG_FILE}' for single-session mode.")
                    sys.exit(1)
            return cfg_json
    except Exception as err:
        print(f"[!] Config load error: {err}")
        sys.exit(1)

async def status_command(ev):
    client = ev.client
    me_id = getattr(client, 'uid', None) or (await client.get_me()).id
    if ev.sender_id != me_id:
        return
        
    chat_id = ev.chat_id
    cid_str = str(chat_id)
    
    m_cfg = get_meow_config(me_id)
    m_mode = m_cfg.get(cid_str, "off")
    if m_mode == "instant":
        meow_st = "🟢 فعال (لحظه‌ای ⚡)"
    elif m_mode == "schedule":
        meow_st = "🟢 فعال (زماندار سرور 📅)"
    else:
        meow_st = "🔴 غیرفعال"
    
    f_cfg = get_fish_cfg(me_id)
    f_mode = f_cfg.get(cid_str, "off")
    fish_st = f"🟢 فعال ({f_mode})" if f_mode != "off" else "🔴 غیرفعال"
    
    fr_cfg = get_fridge_cfg(me_id)
    fr_mode = fr_cfg.get(cid_str, "off")
    fridge_st = f"🟢 فعال ({fr_mode})" if fr_mode != "off" else "🔴 غیرفعال"
    
    c_cfg = get_catch_cfg(me_id).get(cid_str, {})
    catch_st = "🟢 فعال" if c_cfg.get("status") else "🔴 غیرفعال"
    c_delay = c_cfg.get("delay", 0)
    c_times = c_cfg.get("times", 1)
    
    sh_st = "🟢 ON" if get_show_mode(me_id) else "🔴 OFF"

    msg_out = (
        f"🐾 **وضعیت ربات خودکار MeowAce-Self**\n\n"
        f"📍 **چت فعلی:** `{chat_id}`\n\n"
        f"🐱 **AutoMeow:** {meow_st}\n"
        f"🎣 **AutoFish:** {fish_st}\n"
        f"🧊 **AutoFridge:** {fridge_st}\n"
        f"🐈 **AutoCatch:** {catch_st} *(Delay: {c_delay}s, Times: {c_times})*\n"
        f"👁️ **Show Mode:** {sh_st}\n\n"
        f"💡 **دستورات راهنما:**\n"
        f"▸ `/automeow` ── مدیریت ارسال خودکار کلمات میو (instant/schedule/off)\n"
        f"▸ `/autofish` ── مدیریت ماهیگیری خودکار\n"
        f"▸ `/autofridge` ── مدیریت پخت و فروش خودکار یخچال\n"
        f"▸ `/autocatch` ── مدیریت نجات خودکار گربه‌ها\n"
        f"▸ `/show` ── خاموش/روشن کردن پاسخ به دستورات\n"
        f"▸ `/sched` ── زمانبندی پیام روی سرور تلگرام\n"
        f"▸ `/alias` ── تعریف اسم کوتاه و میانبر دستورات\n"
        f"▸ `/status` ── مشاهده وضعیت در این چت"
    )
    await ev.edit(msg_out)

async def run_single_session(conf: dict):
    api_id = conf["api_id"]
    api_hash = conf["api_hash"]
    proxy_kwargs = get_proxy_kwargs(conf)
    
    print("[+] Single-Session: Connecting Telethon client...")
    client = TelegramClient("meowace_self", api_id, api_hash, **proxy_kwargs)
    await client.start()
    
    me = await client.get_me()
    client.uid = me.id
    print(f"[+] Logged in as: {me.first_name} (@{me.username or 'N/A'}) [ID: {me.id}]")

    @client.on(events.NewMessage)
    async def _automeow_schedule_listener(ev):
        await process_schedule_event(ev)

    @client.on(events.NewMessage)
    async def _autocatch_trigger_new(ev):
        await handle_autocatch_trigger(ev, is_edit=False)

    @client.on(events.MessageEdited)
    async def _autocatch_trigger_edit(ev):
        await handle_autocatch_trigger(ev, is_edit=True)

    @client.on(events.NewMessage(pattern='(?i)^/?automeow($|\\s+)'))
    async def _automeow_h(ev):
        await automeow_command(ev)

    @client.on(events.NewMessage(pattern='(?i)^/?autofish($|\\s+)'))
    async def _autofish_h(ev):
        await autofish_command(ev)

    @client.on(events.NewMessage(pattern='(?i)^/?autofridge($|\\s+)'))
    async def _autofridge_h(ev):
        await autofridge_command(ev)

    @client.on(events.NewMessage(pattern='(?i)^/?autocatch($|\\s+)'))
    async def _autocatch_h(ev):
        await autocatch_command(ev)

    @client.on(events.NewMessage(pattern='(?i)^/?show(?:\\s+(.+))?'))
    async def _show_h(ev):
        await show_command(ev)

    @client.on(events.NewMessage(pattern='(?i)^/?sched(?:\\s+(.+))?'))
    async def _sched_h(ev):
        await sched_command(ev)

    @client.on(events.NewMessage(pattern=r'(?i)^[/.=]?alias(?:\s+(.+))?$'))
    async def _alias_h(ev):
        await alias_command(ev)

    @client.on(events.NewMessage(pattern='(?i)^/?(status|meowhelp|help)($|\\s+)'))
    async def _status_h(ev):
        await status_command(ev)

    @client.on(events.NewMessage(outgoing=True))
    async def _alias_interceptor(ev):
        raw = ev.raw_text or ""
        if not raw:
            return
        is_alias, cmds = resolve_alias(client.uid, raw)
        if is_alias and cmds:
            for c in cmds:
                try:
                    await client.send_message(ev.chat_id, c)
                except RPCError as rpc:
                    print(f"[!] alias send error: {rpc}")
                except Exception:
                    pass

    asyncio.create_task(resume_automeow_tasks(client))
    asyncio.create_task(resume_autofish_tasks(client))
    asyncio.create_task(resume_autofridge_tasks(client))
    print("[+] MeowAce-Self single-session client ready.")

    await client.run_until_disconnected()

async def run_multi_session(conf: dict):
    from multisession import resume_all_sessions, subscription_monitor_loop
    from bot_manager import start_bot_manager, bot_client_instance

    print("[+] Multi-Session mode enabled.")
    await resume_all_sessions(conf)

    async def notify_expired(user_id: int, message: str):
        if bot_client_instance and bot_client_instance.is_connected():
            try:
                await bot_client_instance.send_message(user_id, message)
            except Exception as e:
                print(f"[!] Could not send expiration message to {user_id}: {e}")

    asyncio.create_task(subscription_monitor_loop(notify_expired))
    await start_bot_manager(conf)
    
    from bot_manager import bot_client_instance as b_inst
    if b_inst:
        await b_inst.run_until_disconnected()

async def main():
    conf = read_config()
    is_multi = conf.get("multi_session", False)
    
    if is_multi:
        await run_multi_session(conf)
    else:
        await run_single_session(conf)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n[-] Shutting down.")
