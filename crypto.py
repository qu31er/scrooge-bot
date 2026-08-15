import requests
from typing import Optional, Dict, List
import config

class CryptoBot:
    def __init__(self):
        self.token = config.CRYPTO_TOKEN
        self.base_url = 'https://pay.crypt.bot/api'
        self.headers = {
            'Crypto-Pay-API-Token': self.token,
            'Content-Type': 'application/json'
        }
    
    def create_invoice(self, amount: int, asset: str = 'USDT', 
                      description: str = 'Пополнение баланса') -> Optional[Dict]:
        """Создание счета для оплаты"""
        try:
            url = f'{self.base_url}/createInvoice'
            payload = {
                'asset': asset,
                'amount': str(amount),
                'description': description,
                'paid_btn_name': 'openBot',
                'paid_btn_url': 'https://t.me/your_bot'
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            data = response.json()
            
            if data.get('ok'):
                return {
                    'invoice_id': data['result']['invoice_id'],
                    'pay_url': data['result']['pay_url'],
                    'status': data['result']['status'],
                    'amount': data['result']['amount'],
                    'asset': data['result']['asset']
                }
            else:
                print(f"Ошибка создания инвойса: {data}")
                return None
                
        except Exception as e:
            print(f"Ошибка: {e}")
            return None
    
    def check_invoice(self, invoice_id: str) -> Optional[Dict]:
        """Проверка статуса счета"""
        try:
            url = f'{self.base_url}/getInvoices'
            payload = {'invoice_ids': invoice_id}
            
            response = requests.get(url, headers=self.headers, params=payload)
            data = response.json()
            
            if data.get('ok') and data['result']['items']:
                invoice = data['result']['items'][0]
                return {
                    'invoice_id': invoice['invoice_id'],
                    'status': invoice['status'],
                    'amount': invoice['amount'],
                    'asset': invoice['asset'],
                    'paid_at': invoice.get('paid_at'),
                    'user_id': invoice.get('user_id')
                }
            else:
                return None
                
        except Exception as e:
            print(f"Ошибка проверки инвойса: {e}")
            return None
    
    def get_balance(self, asset: str = None) -> Optional[Dict]:
        """Получение баланса кошелька"""
        try:
            url = f'{self.base_url}/getBalance'
            payload = {}
            if asset:
                payload['asset'] = asset
            
            response = requests.get(url, headers=self.headers, params=payload)
            data = response.json()
            
            if data.get('ok'):
                if asset:
                    return {'asset': asset, 'balance': data['result']['balance']}
                return data['result']
            else:
                return None
                
        except Exception as e:
            print(f"Ошибка получения баланса: {e}")
            return None
    
    def transfer(self, user_id: int, amount: int, asset: str = 'USDT', 
                comment: str = 'Вывод средств') -> Optional[Dict]:
        """Перевод средств пользователю"""
        try:
            url = f'{self.base_url}/transfer'
            payload = {
                'user_id': user_id,
                'asset': asset,
                'amount': str(amount),
                'comment': comment
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            data = response.json()
            
            if data.get('ok'):
                return {
                    'transfer_id': data['result']['transfer_id'],
                    'amount': data['result']['amount'],
                    'asset': data['result']['asset'],
                    'status': data['result']['status']
                }
            else:
                print(f"Ошибка перевода: {data}")
                return None
                
        except Exception as e:
            print(f"Ошибка: {e}")
            return None