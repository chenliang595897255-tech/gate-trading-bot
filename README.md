# Gate.io 多源数据交易机器人

本版本从 Gate.io、Binance、Coinbase 获取公开行情，并从公开 RSS 获取新闻标题；随后计算跨源价格一致性和短期动量，生成 BUY/SELL/HOLD 决策。

## 重要安全说明

默认只生成交易提案，不会下单。必须同时满足以下条件才允许 BUY 实盘下单：

```dotenv
DRY_RUN=false
LIVE_TRADING_ENABLED=true
LIVE_CONFIRMATION=I_UNDERSTAND_RISK
```

代码不会读取 Gate.io 登录密码，只使用 API Key/API Secret。API Key 必须关闭提现权限并尽量绑定 IP。新闻和网络数据是不可靠输入，不能保证盈利，也不能自动视为事实。

本版本对 SELL 默认不发送订单，因为卖出前必须同步并验证真实持仓，避免本地状态与交易所状态不一致导致错误下单。

## 安装运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Windows PowerShell：

```powershell
.venv\\Scripts\\activate
pip install -r requirements.txt
Copy-Item .env.example .env
python main.py
```

先保持 `DRY_RUN=true`，观察日志和信号。实盘前还应补充：交易所持仓同步、订单成交确认、精度/最小下单量校验、手续费、限频、断线恢复、持久化和人工急停。
