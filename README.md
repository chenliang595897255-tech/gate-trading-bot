# Gate.io Bot：真实交易系统增强版

本版本增加了基础的生产化交易组件：

- 通过 Gate.io 私有 API 读取余额和锁定余额
- 下单前进行持仓、余额、仓位和每日亏损检查
- 使用客户端订单标识，减少重复下单风险
- 使用原子写入保存本地状态
- 数据源不足时 fail-closed
- 实盘模式和 paper 模式仍然严格分离

## 运行模式

默认使用 paper：

```dotenv
RUN_MODE=paper
LIVE_ARMED=false
LIVE_CONFIRMATION=
```

实盘必须明确设置：

```dotenv
RUN_MODE=live
LIVE_ARMED=true
LIVE_CONFIRMATION=I_UNDERSTAND_RISK
```

API Key 只应开启读取和交易权限，禁止提现，并尽量绑定固定 IP。

## 重要限制

在真正投入资金前仍需完成：

- 下单后订单状态轮询和成交量确认
- 订单超时撤销与重试去重
- 交易所精度、最小数量和最小金额校验
- 手续费、滑点、部分成交和失败订单处理
- 本地状态与交易所账本的定期 reconciliation
- 全局熔断、人工急停、告警和监控
- 只允许白名单交易对

当前代码会先读取真实账户余额再判断风险；但是任何实盘系统都应先在 paper 环境长期运行，并用极小金额进行人工监督测试。

不要把 `.env`、API Secret 或 `data/bot_state.json` 提交到 GitHub。此软件不保证盈利。
