# 交易执行终版（谨慎实盘版）

已加入：

- 下单后状态轮询
- 超时撤单
- 成交数量与均价确认
- 订单 ID 和客户端订单标识
- 最大未完成订单限制
- 余额/持仓重新读取
- 滑点监控
- 数据异常时 fail-closed
- paper/live 严格隔离

## 重要安全通知

此前仓库的 `.env.example` 曾包含看起来像真实 API 密钥的值。即使后来被覆盖，密钥也可能留在 Git 历史中。**请立即在 Gate.io 撤销并重新生成对应 API Key/Secret**，不要继续使用旧密钥。

新配置模板只包含占位符，绝不会要求把密钥提交到仓库。

## 默认运行

```dotenv
RUN_MODE=paper
LIVE_ARMED=false
LIVE_CONFIRMATION=
```

运行：

```bash
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## 实盘闸门

只有你明确承担风险时才设置：

```dotenv
RUN_MODE=live
LIVE_ARMED=true
LIVE_CONFIRMATION=I_UNDERSTAND_RISK
```

实盘前必须：

- 撤销旧 API Key 并创建新 Key
- 关闭提现权限
- 绑定固定 IP
- 使用专门的小额账户
- 设置 `MAX_SLIPPAGE_PERCENT`、`MAX_OPEN_ORDERS` 和每日亏损限制
- 先运行 paper 模式
- 准备人工急停

## 当前仍需人工验收的事项

- Gate.io 的成交字段和状态应在你的账户/环境中验证
- 需要测试最小数量、金额和精度
- 需要确认市场买单 `amount` 的交易所语义和手续费扣除方式
- 需要加入订单成交后真实 PnL 账本
- 需要外部监控、告警和进程守护

任何网络错误、API 错误、数据不足或订单状态不明确都会停止本轮交易。项目不保证盈利。
