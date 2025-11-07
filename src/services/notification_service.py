from src.db.connection import get_db_connection


class NotificationService:

    @staticmethod
    async def create_notification(subscriber_id: int, message: str, type: str, related_url: str):
        """Создает новое уведомление для абонента."""
        conn = await get_db_connection()
        await conn.execute(
            """
            INSERT INTO notifications (subscriber_id, message, type, related_url)
            VALUES ($1, $2, $3, $4)
            """,
            subscriber_id, message, type, related_url
        )
        await conn.close()

    @staticmethod
    async def get_notifications_for_subscriber(subscriber_id: int):
        """Получает все уведомления для абонента."""
        conn = await get_db_connection()
        notifications = await conn.fetch(
            "SELECT * FROM notifications WHERE subscriber_id = $1 ORDER BY sent_date DESC",
            subscriber_id
        )
        await conn.close()
        return notifications

    @staticmethod
    async def mark_notifications_as_read(subscriber_id: int):
        """Отмечает все уведомления для абонента как прочитанные."""
        conn = await get_db_connection()
        await conn.execute(
            "UPDATE notifications SET is_read = TRUE WHERE subscriber_id = $1 AND is_read = FALSE",
            subscriber_id
        )
        await conn.close()

    @staticmethod
    async def count_unread_notifications(subscriber_id: int) -> int:
        """Считает количество непрочитанных уведомлений."""
        conn = await get_db_connection()
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM notifications WHERE subscriber_id = $1 AND is_read = FALSE",
            subscriber_id
        )
        await conn.close()
        return count


notification_service = NotificationService()