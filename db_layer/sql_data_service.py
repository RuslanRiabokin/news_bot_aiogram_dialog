import logging
from db_layer.abstract_database import AbstractDatabase
from typing import List, Tuple

logging.basicConfig(level=logging.INFO)


class SQLDataService:
    """Сервіс для роботи з даними в базі даних."""

    def __init__(self, db: AbstractDatabase):
        self.db = db

    async def __aenter__(self):
        await self.db.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.db.disconnect()

    async def create_db(self):
        """Створює всі необхідні таблиці."""
        await self.db.create_tables()

    async def set_all_sended_status_false(self):
        try:
            await self.db.execute('''
            UPDATE Publish_time
            SET sended = 0
            ''')
            
        except Exception as e:
            logging.error(f"Помилка змінення статусів sended на false: {e}")


    async def set_sended_status_true(self, sub_id, pub_time):
        try:
            await self.db.execute('''
            UPDATE Publish_time
            SET sended = 1
            WHERE sub_id = ? and pub_time = ?
            ''', (sub_id, pub_time))
            
        except Exception as e:
            logging.error(f"Помилка змінення статусу sended на true: {e}")


    async def get_sended_status(self, sub_id, pub_time):
        try:
            return await self.db.fetchone('''
                SELECT sended
                FROM Publish_time
                WHERE sub_id = ? and pub_time = ?
                ''', (sub_id, pub_time))
        except Exception as e:
            logging.error(f"Помилка при отриманні статусу sended: {e}")

    async def add_publish_date(self, sub_id, pub_times):
        try:
            for pub_time in pub_times:
                await self.db.execute('''
                    INSERT INTO Publish_date(sub_id, pub_time)
                    VALUES (?, ?)
                    ''', (sub_id, pub_time))
        except Exception as e:
            logging.error(f"Помилка додавання часу: {e}")
            raise
        

    async def del_publish_date(self, sub_id, pub_time):
        try:
            await self.db.execute('''
                DELETE FROM Publish_date
                WHERE sub_id = ? AND pub_time = ?
                ''', (sub_id, pub_time))
        except Exception as e:
            logging.error(f"Помилка видалення дати: {e}")
            raise
        

    async def get_publish_date(self, sub_id):
        try:
            return await self.db.fetchall('''
                SELECT pub_time
                FROM Publish_date
                WHERE sub_id = ?
            ''', (sub_id, ))
        except Exception as e:
            logging.error(f"Помилка при отриманні дати публікації підписки: {e}")
            raise

    async def delete_dates(self, sub_id):
        try:
            await self.db.execute('''
                        DELETE FROM Publish_date
                        WHERE sub_id = ?
                        ''', (sub_id, ))
        except Exception as e:
            logging.error(f"Помилка видалення дат: {e}")
            raise
        


    async def add_publish_time(self, sub_id, pub_times):
        for pub_time in pub_times:
            try:
                await self.db.execute('''
                    INSERT INTO Publish_time(sub_id, pub_time)
                    VALUES (?, ?)
                    ''', (sub_id, pub_time))

            except Exception as e:
                logging.error(f"Помилка додавання часу: {e}")
                raise
        

    async def del_publish_time(self, sub_id, pub_time):
        try:
            await self.db.execute('''
                DELETE FROM Publish_time
                WHERE sub_id = ? AND pub_time = ?
                ''', (sub_id, pub_time))
        except Exception as e:
            logging.error(f"Помилка видалення часу: {e}")
            raise
        

    async def get_publish_time(self, sub_id):
        try:
            return await self.db.fetchall('''
            SELECT pub_time
            FROM Publish_time
            WHERE sub_id = ?
            ''', (sub_id, ))
        except Exception as e:
            logging.error(f"Помилка при отриманні часу публікації підписки: {e}")
            raise

    async def delete_times(self, sub_id):
        try:
            await self.db.execute('''
                        DELETE FROM Publish_time
                        WHERE sub_id = ?
                        ''', (sub_id, ))
        except Exception as e:
            logging.error(f"Помилка видалення часів: {e}")
            raise
        

    async def insert_news(self, topic_name, channel_name, user_id, news_type='standart',
                          publish_frequency='1h', language_code='ua', add_poll='no',
                          poll_text='a, b, c', is_active='🟢'):
        """Додає новий запис у таблицю News з часом на 1 годину раніше від поточного."""
        if not all([topic_name, channel_name, user_id]):
            raise ValueError("Тема, канал та user_id є обов'язковими.")

        channel_url = channel_name
        try:
            cursor = await self.db.execute('''
            INSERT INTO News (topic_name, channel_name, user_id, publish_frequency,
             news_type, channel_url, language_code, add_poll, poll_text, is_active, last_pub_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '-1 hour'))
            ''', (topic_name, channel_name, user_id, publish_frequency, news_type,
                  channel_url, language_code, add_poll, poll_text, is_active))
            

            news_id = cursor.lastrowid
            return news_id

        except Exception as e:
            logging.error(f"Помилка додавання новини: {e}")
            raise

    async def set_subscription_status(self, status, sub_id: int):
        try:
            await self.db.execute('''
            UPDATE News
            SET is_active = ?
            WHERE id = ?
            ''', (status, sub_id,))
            
        except Exception as e:
            logging.error(f"Помилка при задавані статусу підписки: {e}")
            raise

    async def get_subscription_status(self, sub_id: int):
        try:
            return await self.db.fetchone('''
               SELECT is_active
               FROM News
               WHERE id = ?
               ''', (sub_id,))  # Возвращаем результат для дальнейшей обработки
        except Exception as e:
            logging.error(f"Помилка при отриманні статусу підписки: {e}")
            raise

    async def get_subscriptions(self, user_id: int) -> List[Tuple[int, str, str, str]]:
        """Асинхронно отримує активні підписки користувача з бази даних."""
        query = """
            SELECT id, topic_name, channel_name, last_pub_time, is_active
            FROM News
            WHERE user_id = ? AND (is_active = '🟢' OR is_active = 'pause')
        """
        try:
            subscriptions = await self.db.fetchall(query, (user_id,))
            return subscriptions
        except Exception as e:
            logging.error(f"Помилка отримання підписок: {e}")
            raise

    async def delete_news(self, news_id: int):
        """Деактивує новину за її id."""
        try:
            await self.db.execute('''
            UPDATE News
            SET is_active = 'deactivated'
            WHERE id = ?
            ''', (news_id,))
            
        except Exception as e:
            logging.error(f"Помилка деактивації новини: {e}")
            raise

    import logging

    async def get_user_subscriptions(self, user_id, status='all', search_field=None, search_value=None):
        """Отримує всі підписки користувача за його user_id з можливістю пошуку."""

        # Словник для SQL-запитів на основі статусу
        query_map = {
            'all': '''
                SELECT id, topic_name, channel_name, publish_frequency, news_type, is_active, last_pub_time, add_poll
                FROM News
                WHERE user_id = ?''',
            'active': '''
                SELECT id, topic_name, channel_name, publish_frequency, news_type, is_active, last_pub_time, add_poll
                FROM News
                WHERE user_id = ? AND is_active = '🟢' ''',
            'inactive': '''
                SELECT id, topic_name, channel_name, publish_frequency, news_type, is_active, last_pub_time, add_poll
                FROM News
                WHERE user_id = ? AND is_active = '🔴' '''
        }

        # Отримуємо відповідний SQL-запит для статусу
        query = query_map.get(status)

        if not query:
            raise ValueError("Невірний статус. Доступні варіанти: 'all', 'active', 'inactive'.")

        # Перевірка допустимих полів для пошуку
        allowed_fields = ['topic_name', 'channel_name', 'publish_frequency', 'news_type']
        if search_field and search_field not in allowed_fields:
            raise ValueError(f"Недопустиме поле для пошуку: {search_field}.")


        # Додаємо додаткову умову пошуку, якщо передано поле і значення
        query_params = [user_id]

        if search_field and search_value:
            query += f" AND {search_field} LIKE ?"
            query_params.append(f"%{search_value}%")

        # Логування SQL-запиту
        logging.info(f"Виконання SQL-запиту: {query} з параметрами: {tuple(query_params)}")

        # Виконуємо SQL-запит та повертаємо результат
        try:
            result = await self.db.fetchall(query, tuple(query_params))
            return result
        except Exception as e:
            logging.error(f"Помилка виконання запиту: {e}")
            raise

    async def get_channels_for_publishing(self):
        """Отримує всі канали для публікації новин, якщо остання публікація була понад годину тому."""
        channels = await self.db.fetchall('''
            SELECT id, topic_name, channel_name, user_id, publish_frequency, 
                   news_type, add_poll, poll_text, is_active, last_pub_time
            FROM News
        ''')

        return [
            {
                'id': row[0],
                'topic_name': row[1],
                'channel_name': row[2],
                'user_id': row[3],
                'publish_frequency': row[4],
                'news_type': row[5],
                'add_poll': row[6],
                'poll_text': row[7],
                'is_active': row[8],
                'last_pub_time': row[9]
            }
            for row in channels
        ]

    async def get_last_times_list(self):
        result = await self.db.fetchall('''
            SELECT last_pub_time, topic_name
            FROM News
        ''')

        return [{'last_pub_time': row[0], 'topic_name': row[1]} for row in result]

    async def update_last_published_time(self, topic_id):
        """Оновлює час останньої публікації новини."""
        await self.db.execute('''
        UPDATE News
        SET last_pub_time = datetime('now', 'localtime')
        WHERE id = ?
        ''', (topic_id,))
       

