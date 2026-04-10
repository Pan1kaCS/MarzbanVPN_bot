"""
Интеграция с Marzban API
"""
import requests
import json
from typing import Optional, Dict, Any
import config
from datetime import datetime, timedelta

class MarzbanAPI:
    def __init__(self):
        self.base_url = config.MARZBAN_URL
        self.token = config.MARZBAN_TOKEN
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def _request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        url = f"{self.base_url}/api/user{endpoint}"
        try:
            if method == 'GET':
                resp = requests.get(url, headers=self.headers)
            elif method == 'POST':
                resp = requests.post(url, headers=self.headers, json=data)
            elif method == 'DELETE':
                resp = requests.delete(url, headers=self.headers)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"Marzban API error {endpoint}: {e}")
            return None
    
    def create_user(self, username: str, data_limit_gb: int, expire_days: int) -> Optional[Dict]:
        """Создать пользователя"""
        expire_date = (datetime.utcnow() + timedelta(days=expire_days)).isoformat()
        data = {
            "username": username,
            "data_limit": data_limit_gb * 1024 * 1024 * 1024,  # GB to bytes
            "expire": expire_date
        }
        return self._request('POST', f'/{username}', data)
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Инфо о пользователе"""
        return self._request('GET', f'/{username}')
    
    def delete_user(self, username: str) -> bool:
        """Удалить/заблокировать"""
        result = self._request('DELETE', f'/{username}')
        return result is not None
    
    def get_subscription_url(self, username: str) -> Optional[str]:
        """Подписочная ссылка"""
        user = self.get_user(username)
        if user:
            return f"{config.MARZBAN_URL}/sub/{username}"
        return None

# Глобальный экземпляр
marzban = MarzbanAPI()

if __name__ == '__main__':
    print("Тест Marzban:", marzban.get_user("testuser"))

