import asyncio
import logging
from typing import Dict, List
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database_manager
from config import BOT_TOKEN, NOTIFICATION_SETTINGS

logger = logging.getLogger(__name__)

class AdminPanel:
    def __init__(self, db: database_manager.DatabaseManager, bot: Bot):
        self.db = db
        self.bot = bot
        self.admin_chat_id = NOTIFICATION_SETTINGS.get('admin_chat_id')
        
    def is_admin(self, user_id: int) -> bool:
        """Проверка прав администратора"""
        return str(user_id) == str(self.admin_chat_id)
    
    def get_admin_keyboard(self) -> InlineKeyboardMarkup:
        """Главное меню администратора"""
        builder = InlineKeyboardBuilder()
        builder.button(text="📊 Статистика", callback_data="admin_stats")
        builder.button(text="👥 Пользователи", callback_data="admin_users")
        builder.button(text="💼 Активные сделки", callback_data="admin_active_deals")
        builder.button(text="📋 Все сделки", callback_data="admin_all_deals")
        builder.button(text="💰 Завершить сделку", callback_data="admin_complete_deal")
        builder.button(text="❌ Отменить сделку", callback_data="admin_cancel_deal")
        builder.button(text="📨 Рассылка", callback_data="admin_broadcast")
        builder.button(text="🔒 Заблокировать пользователя", callback_data="admin_block_user")
        builder.adjust(2, 2, 2, 2)
        return builder.as_markup()
    
    async def send_admin_menu(self, chat_id: int):
        """Отправка админского меню"""
        await self.bot.send_message(
            chat_id=chat_id,
            text="🔧 <b>Административная панель Modern Escrow Bot 2025</b>\n\n"
                 "Выберите действие:",
            reply_markup=self.get_admin_keyboard(),
            parse_mode="HTML"
        )
    
    async def show_statistics(self, chat_id: int):
        """Показ статистики бота"""
        stats = await self.db.get_admin_stats()
        
        # Получаем статистику за последние 24 часа
        today_stats = await self._get_today_stats()
        
        text = (
            f"📊 <b>Статистика Modern Escrow Bot</b>\n\n"
            f"👥 Всего пользователей: <b>{stats.get('total_users', 0)}</b>\n"
            f"💼 Активных сделок: <b>{stats.get('active_deals', 0)}</b>\n"
            f"✅ Завершенных сделок: <b>{stats.get('completed_deals', 0)}</b>\n"
            f"💰 Общий объем: <b>{stats.get('total_volume', 0):.2f} USDT</b>\n\n"
            f"📈 <b>За последние 24 часа:</b>\n"
            f"👤 Новых пользователей: <b>{today_stats.get('new_users', 0)}</b>\n"
            f"💼 Новых сделок: <b>{today_stats.get('new_deals', 0)}</b>\n"
            f"✅ Завершенных сделок: <b>{today_stats.get('completed_today', 0)}</b>\n"
            f"💰 Объем за день: <b>{today_stats.get('volume_today', 0):.2f} USDT</b>"
        )
        
        back_button = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
        ])
        
        await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=back_button,
            parse_mode="HTML"
        )
    
    async def show_active_deals(self, chat_id: int):
        """Показ активных сделок"""
        try:
            async with self.db.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        SELECT d.deal_id, d.creator_id, d.buyer_id, d.amount, 
                               d.status, d.created_at, u1.username as creator_username,
                               u2.username as buyer_username
                        FROM deals d
                        LEFT JOIN users u1 ON d.creator_id = u1.user_id
                        LEFT JOIN users u2 ON d.buyer_id = u2.user_id
                        WHERE d.status IN ('active', 'joined', 'paid')
                        ORDER BY d.created_at DESC
                        LIMIT 10
                    """)
                    deals = await cursor.fetchall()
            
            if not deals:
                text = "💼 <b>Активные сделки</b>\n\nНет активных сделок."
            else:
                text = "💼 <b>Активные сделки</b>\n\n"
                for deal in deals:
                    deal_id, creator_id, buyer_id, amount, status, created_at, creator_username, buyer_username = deal
                    status_emoji = {"active": "🟡", "joined": "🔵", "paid": "🟠"}.get(status, "❓")
                    
                    buyer_info = f"@{buyer_username}" if buyer_username else "Ожидание"
                    
                    text += (
                        f"{status_emoji} <code>{deal_id[:8]}...</code>\n"
                        f"💰 {amount} USDT | 👤 @{creator_username} → {buyer_info}\n"
                        f"📅 {created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                    )
            
            back_button = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
            ])
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=back_button,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения активных сделок: {e}")
            await self.bot.send_message(
                chat_id=chat_id,
                text="❌ Ошибка получения данных о сделках"
            )
    
    async def force_complete_deal(self, deal_id: str) -> bool:
        """Принудительное завершение сделки администратором"""
        try:
            # Получаем информацию о сделке
            deal = await self.db.get_deal(deal_id)
            if not deal:
                return False
            
            # Завершаем сделку
            success = await self.db.complete_deal(deal_id)
            
            if success:
                # Уведомляем участников
                await self._notify_deal_completion(deal)
                
                # Логируем действие администратора
                await self.db._log_action(
                    self.admin_chat_id, 
                    deal_id, 
                    "admin_force_complete", 
                    f"Deal forcibly completed by admin"
                )
                
            return success
            
        except Exception as e:
            logger.error(f"Ошибка принудительного завершения сделки {deal_id}: {e}")
            return False
    
    async def force_cancel_deal(self, deal_id: str) -> bool:
        """Принудительная отмена сделки администратором"""
        try:
            # Получаем информацию о сделке
            deal = await self.db.get_deal(deal_id)
            if not deal:
                return False
            
            # Отменяем сделку
            success = await self.db.cancel_deal(deal_id)
            
            if success:
                # Уведомляем участников
                await self._notify_deal_cancellation(deal)
                
                # Логируем действие администратора
                await self.db._log_action(
                    self.admin_chat_id, 
                    deal_id, 
                    "admin_force_cancel", 
                    f"Deal forcibly cancelled by admin"
                )
                
            return success
            
        except Exception as e:
            logger.error(f"Ошибка принудительной отмены сделки {deal_id}: {e}")
            return False
    
    async def broadcast_message(self, message_text: str) -> Dict[str, int]:
        """Рассылка сообщения всем пользователям"""
        try:
            async with self.db.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT user_id FROM users WHERE is_active = TRUE")
                    users = await cursor.fetchall()
            
            sent_count = 0
            failed_count = 0
            
            for user in users:
                try:
                    await self.bot.send_message(
                        chat_id=user[0],
                        text=f"📢 <b>Сообщение от администрации</b>\n\n{message_text}",
                        parse_mode="HTML"
                    )
                    sent_count += 1
                    await asyncio.sleep(0.1)  # Чтобы не превысить лимиты API
                except Exception:
                    failed_count += 1
            
            return {"sent": sent_count, "failed": failed_count}
            
        except Exception as e:
            logger.error(f"Ошибка рассылки: {e}")
            return {"sent": 0, "failed": 0}
    
    async def block_user(self, user_id: int) -> bool:
        """Блокировка пользователя"""
        try:
            async with self.db.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE users SET is_active = FALSE WHERE user_id = %s",
                        (user_id,)
                    )
                    
                    # Отменяем все активные сделки пользователя
                    await cursor.execute(
                        "UPDATE deals SET status = 'cancelled' WHERE (creator_id = %s OR buyer_id = %s) AND status IN ('active', 'joined', 'paid')",
                        (user_id, user_id)
                    )
                    
                    # Логируем действие
                    await self.db._log_action(
                        self.admin_chat_id, 
                        None, 
                        "admin_block_user", 
                        f"User {user_id} blocked by admin"
                    )
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Ошибка блокировки пользователя {user_id}: {e}")
            return False
    
    async def _get_today_stats(self) -> Dict[str, int]:
        """Получение статистики за сегодня"""
        try:
            today = datetime.now().date()
            async with self.db.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    stats = {}
                    
                    # Новые пользователи за сегодня
                    await cursor.execute(
                        "SELECT COUNT(*) FROM users WHERE DATE(registration_date) = %s",
                        (today,)
                    )
                    stats['new_users'] = (await cursor.fetchone())[0]
                    
                    # Новые сделки за сегодня
                    await cursor.execute(
                        "SELECT COUNT(*) FROM deals WHERE DATE(created_at) = %s",
                        (today,)
                    )
                    stats['new_deals'] = (await cursor.fetchone())[0]
                    
                    # Завершенные сделки за сегодня
                    await cursor.execute(
                        "SELECT COUNT(*) FROM deals WHERE DATE(updated_at) = %s AND status = 'completed'",
                        (today,)
                    )
                    stats['completed_today'] = (await cursor.fetchone())[0]
                    
                    # Объем за сегодня
                    await cursor.execute(
                        "SELECT SUM(amount) FROM deals WHERE DATE(updated_at) = %s AND status = 'completed'",
                        (today,)
                    )
                    result = await cursor.fetchone()
                    stats['volume_today'] = float(result[0]) if result[0] else 0.0
                    
                    return stats
                    
        except Exception as e:
            logger.error(f"Ошибка получения статистики за сегодня: {e}")
            return {}
    
    async def _notify_deal_completion(self, deal: Dict):
        """Уведомление о завершении сделки"""
        try:
            completion_message = (
                f"✅ <b>Сделка завершена администратором</b>\n\n"
                f"🆔 ID: <code>{deal['deal_id']}</code>\n"
                f"💰 Сумма: {deal['amount']} USDT\n"
                f"📝 Условие: {deal['condition']}"
            )
            
            # Уведомляем создателя
            await self.bot.send_message(
                chat_id=deal['creator_id'],
                text=completion_message,
                parse_mode="HTML"
            )
            
            # Уведомляем покупателя, если есть
            if deal['buyer_id']:
                await self.bot.send_message(
                    chat_id=deal['buyer_id'],
                    text=completion_message,
                    parse_mode="HTML"
                )
                
        except Exception as e:
            logger.error(f"Ошибка уведомления о завершении сделки: {e}")
    
    async def _notify_deal_cancellation(self, deal: Dict):
        """Уведомление об отмене сделки"""
        try:
            cancellation_message = (
                f"❌ <b>Сделка отменена администратором</b>\n\n"
                f"🆔 ID: <code>{deal['deal_id']}</code>\n"
                f"💰 Сумма: {deal['amount']} USDT\n"
                f"📝 Условие: {deal['condition']}"
            )
            
            # Уведомляем создателя
            await self.bot.send_message(
                chat_id=deal['creator_id'],
                text=cancellation_message,
                parse_mode="HTML"
            )
            
            # Уведомляем покупателя, если есть
            if deal['buyer_id']:
                await self.bot.send_message(
                    chat_id=deal['buyer_id'],
                    text=cancellation_message,
                    parse_mode="HTML"
                )
                
        except Exception as e:
            logger.error(f"Ошибка уведомления об отмене сделки: {e}")