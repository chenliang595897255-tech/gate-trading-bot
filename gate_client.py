import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import urlencode

import requests


class GateClient:
    prefix = "/api/v4"

    def __init__(self, key: str, secret: str, base_url: str, timeout: int):
        self.key, self.secret = key, secret
        self.base_url, self.timeout = base_url.rstrip("/"), timeout
        self.session = requests.Session()

    def _request(self, method: str, endpoint: str, params=None, body=None, private=False):
        params = params or {}
        query = urlencode(params)
        text = json.dumps(body, separators=(",", ":"), ensure_ascii=False) if body is not None else ""
        path = self.prefix + endpoint
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if private:
            timestamp = str(int(time.time()))
            message = f"{timestamp}\n{method.upper()}\n{path}\n{query}\n{text}\n"
            sign = hmac.new(self.secret.encode(), message.encode(), hashlib.sha512).hexdigest()
            headers.update({"KEY": self.key, "Timestamp": timestamp, "SIGN": sign})
        url = self.base_url + path + (("?" + query) if query else "")
        response = self.session.request(method, url, headers=headers, data=text or None, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def ticker(self, pair: str) -> float:
        data = self._request("GET", "/spot/tickers", {"currency_pair": pair})
        return float(data[0]["last"])

    def accounts(self):
        return self._request("GET", "/spot/accounts", private=True)

    def currency_pair(self, pair: str):
        return self._request("GET", f"/spot/currency_pairs/{pair}")

    def order(self, order_id: str, pair: str):
        return self._request("GET", f"/spot/orders/{order_id}", {"currency_pair": pair}, private=True)

    def open_orders(self, pair: str):
        return self._request("GET", "/spot/open_orders", {"currency_pair": pair}, private=True)

    def market_order(self, pair: str, side: str, amount: str, client_order_id: str | None = None, account="spot"):
        body = {
            "currency_pair": pair,
            "type": "market",
            "account": account,
            "side": side,
            "amount": amount,
        }
        if client_order_id:
            body["text"] = client_order_id
        return self._request("POST", "/spot/orders", body=body, private=True)
