# Gate.io Bot：回测、模拟盘、实盘严格分离

本项目现在有两条完全不同的路径：

- `backtest.py`：离线读取 CSV，只做历史回测，不加载 API 密钥，也不联网下单。
- `main.py` + `RUN_MODE=paper`：读取实时公开数据，只输出交易提案，不下单。
- `main.py` + `RUN_MODE=live`：只有显式完成多重安全确认后才允许发送 Gate.io 买单。

## 1. 离线回测

准备一个至少含有 `close` 列的 CSV：

```csv
close
100
101
...
```

运行：

```bash
python backtest.py prices.csv --cash 1000 --order-usdt 20 --fee 0.001
```

回测只用于评估策略，不代表未来收益。不要把回测收益直接当作实盘预期。

## 2. 模拟盘 / paper 模式

复制配置：

```bash
cp .env.example .env
```

必须保持：

```dotenv
RUN_MODE=paper
LIVE_ARMED=false
LIVE_CONFIRMATION=
```

运行：

```bash
python main.py
```

该模式可以读取行情和新闻，但只记录 `PAPER PROPOSAL ONLY`，不会调用下单接口。

## 3. 实盘模式安全闸门

实盘不是默认模式。必须明确设置全部值：

```dotenv
RUN_MODE=live
LIVE_ARMED=true
LIVE_CONFIRMATION=I_UNDERSTAND_RISK
GATE_API_KEY=你的API_Key
GATE_API_SECRET=你的API_Secret
```

启动前请确认：

- API Key 没有提现权限
- API Key 尽量绑定固定 IP
- 使用独立小额账户
- 已完成回测和足够长时间的 paper 验证
- 已设置单笔额度、最大仓位、每日最大亏损
- 已准备人工急停和日志监控

程序在实盘模式下仍然会阻止 SELL，直到实现真实持仓同步、订单成交确认和部分成交处理；这是故意的安全限制。

## 4. 当前限制

- 回测是简化的收盘价模型，未模拟滑点和订单簿深度。
- 多源行情可能存在延迟、缺失或格式差异。
- 新闻只作为记录信息，不能证明方向。
- 当前实盘路径未完成持仓 reconciliation，因此不允许卖出。
- 任何配置错误、数据源不一致或网络异常都应保持不交易。

不要把 `.env` 提交到 GitHub，也不要在聊天中发送 API Secret。此项目不保证盈利。
