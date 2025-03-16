import json
import aiohttp
import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class BaleClient:
    """کلاینت API بله"""
    
    def __init__(self, token: str, base_url: str = "https://tapi.bale.ai/bot"):
        """مقداردهی اولیه"""
        self.token = token
        self.base_url = base_url
        self.session = None
        
    async def _ensure_session(self):
        """اطمینان از وجود نشست HTTP"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            
    async def _make_request(self, method: str, data: Optional[Dict] = None) -> Dict:
        """ارسال درخواست به API بله"""
        await self._ensure_session()
        
        url = f"{self.base_url}{self.token}/{method}"
        logger.info(f"Making request to Bale API: {method}, data: {data}")
        
        try:
            async with self.session.post(url, json=data) as response:
                result = await response.json()
                logger.info(f"Bale API response: {result}")
                return result
        except Exception as e:
            logger.error(f"Error making request to Bale API: {str(e)}", exc_info=True)
            return {"ok": False, "description": str(e)}
            
    async def get_updates(self, offset: Optional[int] = None, timeout: int = 60) -> Dict:
        """دریافت آپدیت‌های جدید"""
        data = {"timeout": timeout}
        if offset is not None:
            data["offset"] = offset
            
        logger.info(f"Getting updates with offset: {offset}, timeout: {timeout}")
        return await self._make_request("getUpdates", data)
        
    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        components: Optional[Union[str, Dict]] = None
    ) -> Dict:
        """ارسال پیام"""
        data = {
            "chat_id": chat_id,
            "text": text
        }
        
        if components:
            logger.info(f"Sending message with components: {components}")
            if isinstance(components, dict):
                components = json.dumps(components)
            data["reply_markup"] = components
        else:
            logger.info(f"Sending message without components")
            
        logger.info(f"Sending message to chat_id: {chat_id}, text: {text[:50]}...")
        return await self._make_request("sendMessage", data)
        
    async def edit_message_text(
        self,
        chat_id: Union[int, str],
        message_id: int,
        text: str,
        components: Optional[Union[str, Dict]] = None
    ) -> Dict:
        """ویرایش متن پیام"""
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text
        }
        
        if components:
            logger.info(f"Editing message with components: {components}")
            if isinstance(components, dict):
                components = json.dumps(components)
            data["reply_markup"] = components
        else:
            logger.info(f"Editing message without components")
            
        logger.info(f"Editing message for chat_id: {chat_id}, message_id: {message_id}, text: {text[:50]}...")
        return await self._make_request("editMessageText", data)
        
    async def get_file(self, file_id: str) -> Dict:
        """دریافت اطلاعات فایل"""
        return await self._make_request("getFile", {"file_id": file_id})
        
    async def download_file(self, file_path: str) -> bytes:
        """دانلود فایل"""
        await self._ensure_session()
        
        url = f"https://tapi.bale.ai/file/bot{self.token}/{file_path}"
        
        try:
            async with self.session.get(url) as response:
                return await response.read()
        except Exception as e:
            logger.error(f"Error downloading file from Bale: {str(e)}")
            return None
            
    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False
    ) -> Dict:
        """پاسخ به کالبک کوئری"""
        data = {"callback_query_id": callback_query_id}
        
        if text:
            data["text"] = text
        if show_alert:
            data["show_alert"] = show_alert
            
        return await self._make_request("answerCallbackQuery", data)
        
    def create_keyboard(
        self,
        buttons: List[List[Dict[str, str]]],
        inline: bool = False
    ) -> Dict:
        """ایجاد کیبورد"""
        if inline:
            return {
                "inline_keyboard": buttons
            }
        else:
            return {
                "keyboard": buttons,
                "resize_keyboard": True,
                "one_time_keyboard": False
            }
            
    async def close(self):
        """بستن نشست HTTP"""
        if self.session:
            await self.session.close()
            self.session = None 