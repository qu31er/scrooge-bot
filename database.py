import sqlite3
from typing import Optional, List, Dict

class Database:
    def __init__(self, db_path='main.db'):
        self.db_path = db_path
        self.init_tables()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    name TEXT,
                    status TEXT DEFAULT 'User',
                    balance INTEGER DEFAULT 0,
                    buy INTEGER DEFAULT 0,
                    buy_sum INTEGER DEFAULT 0,
                    sell INTEGER DEFAULT 0,
                    sell_sum INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    channal TEXT DEFAULT '@your_channel',
                    commission INTEGER DEFAULT 5,
                    help TEXT DEFAULT 'Бот для безопасных сделок'
                );

                CREATE TABLE IF NOT EXISTS sale (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT,
                    name TEXT,
                    user_id2 TEXT,
                    name2 TEXT,
                    sum INTEGER,
                    status TEXT DEFAULT 'pending',
                    crypto_invoice_id TEXT
                );

                CREATE TABLE IF NOT EXISTS dispute (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT,
                    name TEXT,
                    user_id2 TEXT,
                    name2 TEXT,
                    sum INTEGER,
                    status TEXT DEFAULT 'pending'
                );

                CREATE TABLE IF NOT EXISTS post (
                    text TEXT,
                    key TEXT
                );

                CREATE TABLE IF NOT EXISTS feedback (
                    user_id TEXT,
                    name TEXT,
                    name2 TEXT,
                    text TEXT,
                    rating INTEGER DEFAULT 5
                );

                CREATE TABLE IF NOT EXISTS donate (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    sum INTEGER,
                    crypto_invoice_id TEXT
                );

                CREATE TABLE IF NOT EXISTS crypto_invoices (
                    invoice_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    amount REAL,
                    asset TEXT DEFAULT 'USDT',
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deal_id INTEGER DEFAULT 0,
                    type TEXT DEFAULT 'deposit'
                );
            ''')
            
            settings = cursor.execute('SELECT * FROM settings WHERE id = 1').fetchone()
            if not settings:
                cursor.execute('''
                    INSERT INTO settings (id, channal, commission, help)
                    VALUES (1, ?, ?, ?)
                ''', ('@your_channel', 5, 'Бот для безопасных сделок'))
            
            counter = cursor.execute('SELECT * FROM sale WHERE id = 0').fetchone()
            if not counter:
                cursor.execute('''
                    INSERT INTO sale (id, user_id, name, user_id2, name2, sum, status)
                    VALUES (0, '0', 'system', '0', 'system', 0, 'system')
                ''')
            
            post = cursor.execute('SELECT * FROM post').fetchone()
            if not post:
                cursor.execute('''
                    INSERT INTO post (text, key) 
                    VALUES (?, ?)
                ''', (
                    '<b>Добро пожаловать!</b>\n\nБезопасные сделки с криптовалютой.',
                    '[Канал + https://t.me/your_channel]'
                ))
            
            conn.commit()
    
    #ПОЛЬЗОВАТЕЛИ
  
    def add_user(self, user_id: int, username: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO users (user_id, name) VALUES (?, ?)',
                    (str(user_id), username.lower())
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (str(user_id),))
            row = cursor.fetchone()
            if row:
                return {
                    'user_id': row[0],
                    'name': row[1],
                    'status': row[2],
                    'balance': row[3],
                    'buy': row[4],
                    'buy_sum': row[5],
                    'sell': row[6],
                    'sell_sum': row[7]
                }
            return None
    
    def get_user_by_name(self, username: str) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE name = ?', (username.lower(),))
            row = cursor.fetchone()
            if row:
                return {
                    'user_id': row[0],
                    'name': row[1],
                    'status': row[2],
                    'balance': row[3],
                    'buy': row[4],
                    'buy_sum': row[5],
                    'sell': row[6],
                    'sell_sum': row[7]
                }
            return None
    
    def update_balance(self, user_id: int, amount: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET balance = balance + ? WHERE user_id = ?',
                (amount, str(user_id))
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def set_balance(self, user_id: int, amount: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET balance = ? WHERE user_id = ?',
                (amount, str(user_id))
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def get_all_users(self) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users')
            rows = cursor.fetchall()
            return [{
                'user_id': row[0],
                'name': row[1],
                'status': row[2],
                'balance': row[3],
                'buy': row[4],
                'buy_sum': row[5],
                'sell': row[6],
                'sell_sum': row[7]
            } for row in rows]
    
     #СДЕЛКИ
    
    def create_sale(self, user_id: int, name: str, user_id2: int, name2: str, amount: int) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            counter = cursor.execute('SELECT id FROM sale WHERE user_id = "0"').fetchone()
            new_id = counter[0] + 1
            cursor.execute('UPDATE sale SET id = ? WHERE user_id = "0"', (new_id,))
            
            cursor.execute('''
                INSERT INTO sale (id, user_id, name, user_id2, name2, sum, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (new_id, str(user_id), name, str(user_id2), name2, amount, 'pending'))
            
            cursor.execute(
                'UPDATE users SET balance = balance - ? WHERE user_id = ?',
                (amount, str(user_id))
            )
            conn.commit()
            return new_id
    
    def get_sale(self, sale_id: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sale WHERE id = ?', (sale_id,))
            row = cursor.fetchone()
            if row and row[0] != 0:
                return {
                    'id': row[0],
                    'user_id': row[1],
                    'name': row[2],
                    'user_id2': row[3],
                    'name2': row[4],
                    'sum': row[5],
                    'status': row[6],
                    'crypto_invoice_id': row[7] if len(row) > 7 else None
                }
            return None
    
    def get_user_sales(self, user_id: int) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM sale WHERE (user_id = ? OR user_id2 = ?) AND id != 0 AND status != "completed"',
                (str(user_id), str(user_id))
            )
            rows = cursor.fetchall()
            return [{
                'id': row[0],
                'user_id': row[1],
                'name': row[2],
                'user_id2': row[3],
                'name2': row[4],
                'sum': row[5],
                'status': row[6]
            } for row in rows]
    
    def complete_sale(self, sale_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sale = self.get_sale(sale_id)
            if not sale:
                return False
            
            settings = self.get_settings()
            commission_amount = int(sale['sum'] * settings['commission'] / 100)
            seller_amount = sale['sum'] - commission_amount
            
            cursor.execute(
                'UPDATE users SET balance = balance + ? WHERE user_id = ?',
                (seller_amount, sale['user_id2'])
            )
            cursor.execute(
                'UPDATE users SET buy = buy + 1, buy_sum = buy_sum + ? WHERE user_id = ?',
                (sale['sum'], sale['user_id'])
            )
            cursor.execute(
                'UPDATE users SET sell = sell + 1, sell_sum = sell_sum + ? WHERE user_id = ?',
                (seller_amount, sale['user_id2'])
            )
            cursor.execute(
                'UPDATE sale SET status = ? WHERE id = ?',
                ('completed', sale_id)
            )
            conn.commit()
            return True
    
    def cancel_sale(self, sale_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sale = self.get_sale(sale_id)
            if not sale:
                return False
            
            cursor.execute(
                'UPDATE users SET balance = balance + ? WHERE user_id = ?',
                (sale['sum'], sale['user_id'])
            )
            cursor.execute(
                'UPDATE sale SET status = ? WHERE id = ?',
                ('cancelled', sale_id)
            )
            conn.commit()
            return True
    
    #КОНФЛИКТЫ
    
    def create_dispute(self, sale_id: int, user_id: int, name: str, user_id2: int, name2: str, amount: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sale WHERE id = ?', (sale_id,))
            cursor.execute('''
                INSERT INTO dispute (id, user_id, name, user_id2, name2, sum, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (sale_id, str(user_id), name, str(user_id2), name2, amount, 'pending'))
            conn.commit()
            return True
    
    def get_dispute(self, dispute_id: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM dispute WHERE id = ?', (dispute_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'user_id': row[1],
                    'name': row[2],
                    'user_id2': row[3],
                    'name2': row[4],
                    'sum': row[5],
                    'status': row[6]
                }
            return None
    
    def resolve_dispute(self, dispute_id: int, winner_user_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            dispute = self.get_dispute(dispute_id)
            if not dispute:
                return False
            
            cursor.execute(
                'UPDATE users SET balance = balance + ? WHERE user_id = ?',
                (dispute['sum'], str(winner_user_id))
            )
            cursor.execute(
                'UPDATE dispute SET status = ? WHERE id = ?',
                ('resolved', dispute_id)
            )
            conn.commit()
            return True
    
    #НАСТРОЙКИ
    
    def get_settings(self) -> Dict:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM settings WHERE id = 1')
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'channal': row[1],
                    'commission': row[2],
                    'help': row[3]
                }
            return {'commission': 5, 'channal': '@your_channel', 'help': 'Бот для безопасных сделок'}
    
    def update_setting(self, key: str, value) -> bool:
        allowed_keys = ['channal', 'commission', 'help']
        if key not in allowed_keys:
            return False
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE settings SET {key} = ? WHERE id = 1', (value,))
            conn.commit()
            return cursor.rowcount > 0
    
    #ПОСТЫ
    
    def get_post(self) -> Dict:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM post')
            row = cursor.fetchone()
            if row:
                return {'text': row[0], 'buttons': row[1]}
            return {'text': '<b>Добро пожаловать!</b>', 'buttons': ''}
    
    def update_post(self, text: str, buttons: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM post')
            cursor.execute('INSERT INTO post VALUES (?, ?)', (text, buttons))
            conn.commit()
            return True
   
    #ОТЗЫВЫ
    
    def add_feedback(self, user_id: int, name: str, name2: str, text: str, rating: int = 5) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO feedback (user_id, name, name2, text, rating)
                VALUES (?, ?, ?, ?, ?)
            ''', (str(user_id), name, name2, text, rating))
            conn.commit()
            return True
    
    def get_feedback(self, user_id: int) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM feedback WHERE user_id = ? ORDER BY rowid DESC LIMIT 10
            ''', (str(user_id),))
            rows = cursor.fetchall()
            return [{
                'user_id': row[0],
                'name': row[1],
                'name2': row[2],
                'text': row[3],
                'rating': row[4]
            } for row in rows]
    
    #ДОНАТЫ
    
    def add_donate(self, user_id: int, amount: int, invoice_id: str = None) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO donate (user_id, sum, crypto_invoice_id)
                VALUES (?, ?, ?)
            ''', (str(user_id), amount, invoice_id))
            conn.commit()
            return True
    
    def get_top_donates(self, limit: int = 5) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, SUM(sum) as total 
                FROM donate 
                GROUP BY user_id 
                ORDER BY total DESC 
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [{'user_id': row[0], 'total': row[1]} for row in rows]
    
    #ИНВОЙСЫ
    
    def add_invoice(self, invoice_id: str, user_id: int, amount: int, asset: str = 'USDT', 
                   deal_id: int = 0, type: str = 'deposit') -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO crypto_invoices (invoice_id, user_id, amount, asset, deal_id, type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (invoice_id, str(user_id), amount, asset, deal_id, type))
            conn.commit()
            return True
    
    def get_invoice(self, invoice_id: str) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM crypto_invoices WHERE invoice_id = ?', (invoice_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'invoice_id': row[0],
                    'user_id': row[1],
                    'amount': row[2],
                    'asset': row[3],
                    'status': row[4],
                    'created_at': row[5],
                    'deal_id': row[6],
                    'type': row[7]
                }
            return None
    
    def update_invoice_status(self, invoice_id: str, status: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE crypto_invoices SET status = ? WHERE invoice_id = ?',
                (status, invoice_id)
            )
            conn.commit()
            return cursor.rowcount > 0