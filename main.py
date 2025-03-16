from src.bale import BaleClient
import asyncio
import aiohttp
import logging
from typing import Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta

# Define conversation states
PHONE, OTP = range(4)
BALE_BOT_TOKEN="TOKEN"

class BaleBot:
    def __init__(self):
        """Initialize the bot"""
        self.client = BaleClient(token=BALE_BOT_TOKEN)
        self.user_data = {}
        self.offset = None
        self.scheduler = AsyncIOScheduler()
        self.jobs = {}
        
    async def handle_update(self, update: Dict[str, Any]):
        """پردازش آپدیت‌های دریافتی"""
        if "message" in update:
            message = update["message"]

            #TODO handle any things. some process is: 
            if "contact" in message:
                await self.handle_contact(message)
            elif "document" in message:
                document = message["document"]
                mime_type = document.get("mime_type", "")
                # handle your mime type
            elif "text" in message:
                text = message["text"]
                if text.startswith("/start"):
                    await self.start_command(message)
                elif text == "💰 شارژ کیف پول":
                    await self.handle_charge_wallet(message)
                elif text == "📊 وضعیت حساب":
                    await self.show_main_menu(message)
                else:
                    user_id = message["from"]["id"]
                    user_data = self.user_data.get(user_id, {})
                    state = user_data.get("state")
                    
                    if state == OTP:
                        await self.handle_otp(message)
        
        elif "callback_query" in update:
            callback = update["callback_query"]
            data = callback["data"]
            
            if data.startswith("pay_"):
                await self.handle_payment_callback(callback)
    
    async def run(self):
        """اجرای اصلی ربات"""
        logger.info("Starting Bale bot...")
        
        # شروع زمانبند
        self.scheduler.start()
        
        try:
            while True:
                try:
                    updates = await self.client.get_updates(offset=self.offset)
                    
                    if updates.get("ok"):
                        for update in updates.get("result", []):
                            await self.handle_update(update)
                            # به‌روزرسانی offset برای دریافت پیام‌های جدید
                            self.offset = update["update_id"] + 1
                    
                except Exception as e:
                    logger.error(f"Error in main loop: {str(e)}")
                
                await asyncio.sleep(1)
        finally:
            # اطمینان از توقف زمانبند در صورت خروج از حلقه
            self.scheduler.shutdown()
            # بستن نشست HTTP
            await self.client.close()
            logger.info("Bot resources cleaned up")

    async def schedule_job_check(self, phone: str, chat_id: int, message_id: int = None):
        """برنامه‌ریزی بررسی وضعیت پردازش """

        # TODO checking some file process and after done use this:
    
        self.scheduler.remove_job(job_id)
        self.jobs.pop(job_id, None) 
        pass

    async def start_command(self, message: Dict[str, Any]):
        """پردازش دستور /start"""
        user_id = message["from"]["id"]
        
        keyboard = self.client.create_keyboard([
            [{"text": "📱 ارسال شماره تلفن", "request_contact": True}]
        ])
        
        await self.client.send_message(
            chat_id=user_id,
            text="👋 به ربات تبدیل خوش آمدید!\n\n"
                    "برای استفاده از ربات، لطفاً شماره تلفن خود را به اشتراک بگذارید:",
            components=keyboard
        )

    async def handle_charge_wallet(self, message: Dict[str, Any]):
        """پردازش درخواست شارژ کیف پول"""
            
        try:
            # ساخت کیبورد با مبالغ پیش‌فرض
            keyboard = self.client.create_keyboard([
                [
                    {"text": "💳 ۵۰,۰۰۰ تومان", "callback_data": "pay_50000"},
                    {"text": "💳 ۱۰۰,۰۰۰ تومان", "callback_data": "pay_100000"}
                ],
                [
                    {"text": "💳 ۲۰۰,۰۰۰ تومان", "callback_data": "pay_200000"},
                    {"text": "💳 ۵۰۰,۰۰۰ تومان", "callback_data": "pay_500000"}
                ]
            ], inline=True)
            
            await self.client.send_message(
                chat_id=user_id,
                text="💰 لطفاً مبلغ مورد نظر برای شارژ کیف پول را انتخاب کنید:",
                components=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error handling charge wallet: {str(e)}")
            await self.client.send_message(
                chat_id=user_id,
                text="متأسفانه در پردازش درخواست شارژ مشکلی پیش آمد. لطفاً دوباره تلاش کنید."
            )

    async def handle_payment_callback(self, callback: Dict[str, Any]):
        """پردازش کالبک پرداخت"""
        # TODO complate payment for user.
        pass

    async def show_main_menu(self, message: Dict[str, Any]):
        """نمایش منوی اصلی و وضعیت حساب"""
        user_id = message["from"]["id"]
        try:
            
            text = (
                f"💰 موجودی کیف پول: {1000000:,} تومان\n"
                "از منوی زیر انتخاب کنید:"
            )
            
            # ساخت کیبورد
            keyboard = self.client.create_keyboard([
                [{"text": "💰 شارژ کیف پول"}],
                [{"text": "📊 وضعیت حساب"}]
            ])
            
            await self.client.send_message(
                chat_id=user_id,
                text=text,
                components=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error showing main menu: {str(e)}")
            await self.client.send_message(
                chat_id=user_id,
                text="متأسفانه در نمایش وضعیت حساب مشکلی پیش آمد. لطفاً دوباره تلاش کنید."
            )
    
    async def handle_contact(self, message: Dict[str, Any]):
        """پردازش اطلاعات تماس دریافتی"""
        user_id = message["from"]["id"]
        contact = message["contact"]
        
        if self.user_data.get(user_id, {}).get("state") != PHONE:
            return
        
        # دریافت شماره تلفن از اطلاعات تماس
        phone = contact["phone_number"]
            
        logger.info(f"Received contact with phone {phone} for user {user_id}")
            
        try:
            if phone.startswith('+98') or phone.startswith('98'):
                phone = phone.replace('+98', '0', 1).replace('98', '0', 1)

            # ذخیره شماره تلفن و تغییر وضعیت به OTP
            self.user_data[user_id] = {
                "state": OTP,
                "phone": phone
            }
        
            # TODO send otp message or proccess   
        except Exception as e:
            logger.error(f"Error requesting OTP: {str(e)}")
            await self.client.send_message(
                chat_id=user_id,
                text="متأسفانه در ارسال کد تأیید مشکلی پیش آمد. لطفاً دوباره تلاش کنید."
            )
            # پاک کردن اطلاعات کاربر
            self.user_data.pop(user_id, None)

    async def handle_otp(self, message: Dict[str, Any]):
        """پردازش کد OTP دریافتی"""
        user_id = message["from"]["id"]
        otp = message["text"]
        user_data = self.user_data.get(user_id)
        
        if not user_data or user_data.get("state") != OTP:
            return
            
        phone = user_data.get("phone")
        if not phone:
            return
        
        # TODO check otp message to run sample job.

        job = self.scheduler.add_job(
            self.schedule_job_check,
            trigger=IntervalTrigger(seconds=15), 
            args=[phone, user_id, message_id],
            id=job_id,
            max_instances=1,
            replace_existing=True,
            next_run_time=datetime.now()  
        )
        
        self.jobs[job_id] = {
            "job": job,
            "start_time": datetime.now(),
            "max_duration": timedelta(minutes=15),
            "phone": phone,
            "user_id": user_id,
            "message_id": message_id
        }


def main():
    """تابع اصلی برای راه‌اندازی ربات"""
    # تنظیمات لاگینگ
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # ایجاد نمونه ربات
    bot = BaleBot()
    
    # راه‌اندازی ربات
    try:
        # استفاده از asyncio.run برای اجرای کورتین اصلی
        # این تابع یک حلقه رویداد جدید ایجاد می‌کند
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
