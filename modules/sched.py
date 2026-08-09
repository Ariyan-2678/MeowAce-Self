import time
from telethon.errors import RPCError
from modules.utils import convert_persian_digits

async def sched_command(ev):
    client = ev.client
    me_id = getattr(client, 'uid', None) or (await client.get_me()).id
    if ev.sender_id != me_id:
        return
        
    raw = convert_persian_digits(ev.raw_text or "")
    parts = raw.split(maxsplit=3)
    
    if len(parts) < 4:
        await ev.edit(
            "⏰ **دستور زمانبندی پیام (Telegram Scheduled Messages)**\n\n"
            "💡 **توضیحات:**\n"
            "زمانبندی یک پیام دلخواه بر روی سرورهای تلگرام جهت آنلاین نشدن اکانت در کامندهایی نظیر automeow.\n\n"
            "📖 **نحوه استفاده:**\n"
            "`/sched [تعداد] [فاصله به دقیقه] [متن پیام]`\n\n"
            "📌 **مثال:**\n"
            "`/sched 10 5 میو`"
        )
        return
        
    try:
        cnt = int(parts[1])
        interval = int(parts[2])
        txt = parts[3].strip()
    except ValueError:
        await ev.edit("⚠️ **خطا:** تعداد و فاصله زمانی باید عدد صحیح باشند.")
        return

    if cnt <= 0 or interval <= 0:
        await ev.edit("⚠️ **خطا:** تعداد و فاصله زمانی باید بزرگتر از صفر باشند.")
        return

    if cnt > 100:
        await ev.edit("⚠️ **حداکثر تعداد پیام مجاز برای زمانبندی ۱۰۰ عدد می‌باشد.**")
        return

    await ev.edit("⏰ **در حال ثبت زمانبندی پیام‌ها بر روی سرور تلگرام...**")

    t_now = int(time.time())
    done = 0
    
    for i in range(1, cnt + 1):
        target_time = t_now + (i * interval * 60)
        try:
            await client.send_message(
                ev.chat_id,
                txt,
                schedule=target_time
            )
            done += 1
        except RPCError as rpc:
            print(f"[!] schedule error at index {i}: {rpc}")
        except Exception:
            pass

    await ev.edit(
        f"✅ **با موفقیت تعداد `{done}` پیام زمانبندی شد!**\n"
        f"⏱️ هر `{interval}` دقیقه یک‌بار پیام `{txt}` ارسال خواهد شد."
    )
