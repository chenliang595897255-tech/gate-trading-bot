import logging
import time


class ExecutionError(RuntimeError):
    pass


class ExecutionEngine:
    TERMINAL = {"closed", "cancelled", "expired", "failed"}

    def __init__(self, client, pair, poll_seconds=2, timeout_seconds=30, max_slippage_percent=0.5):
        self.client = client
        self.pair = pair
        self.poll_seconds = poll_seconds
        self.timeout_seconds = timeout_seconds
        self.max_slippage_percent = max_slippage_percent

    @staticmethod
    def _filled(order):
        return float(order.get("filled_amount", 0) or 0)

    @staticmethod
    def _avg_price(order):
        amount = float(order.get("filled_amount", 0) or 0)
        total = float(order.get("filled_total", 0) or 0)
        return total / amount if amount > 0 else None

    def submit_and_confirm(self, side, amount, client_order_id, reference_price):
        order = self.client.market_order(self.pair, side, amount, client_order_id)
        order_id = str(order.get("id", ""))
        if not order_id:
            raise ExecutionError("exchange returned no order id")

        deadline = time.monotonic() + self.timeout_seconds
        latest = order
        while time.monotonic() < deadline:
            latest = self.client.order(order_id, self.pair)
            status = latest.get("status", "")
            if status in self.TERMINAL:
                break
            time.sleep(self.poll_seconds)

        status = latest.get("status", "")
        if status not in self.TERMINAL:
            try:
                self.client.cancel_order(order_id, self.pair)
            except Exception:
                logging.exception("cancel failed for timed-out order %s", order_id)
            raise ExecutionError(f"order {order_id} timed out")

        filled = self._filled(latest)
        if filled <= 0:
            raise ExecutionError(f"order {order_id} has no fill; status={status}")

        average = self._avg_price(latest)
        if average and reference_price > 0:
            slippage = abs(average - reference_price) / reference_price * 100
            if slippage > self.max_slippage_percent:
                logging.error("order %s exceeded slippage: %.3f%%", order_id, slippage)

        logging.info("order confirmed id=%s status=%s filled=%s average=%s", order_id, status, filled, average)
        return latest
