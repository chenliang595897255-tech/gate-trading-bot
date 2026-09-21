# Gate.io Bot：多源数据增强

当前数据层从以下公开来源获取行情：

- Gate.io
- Binance
- Kraken
- Coinbase

资讯层读取公开 RSS：

- CoinDesk
- Cointelegraph
- Decrypt

系统使用中位数价格、跨平台价格离散度和 24 小时动量生成信号。新闻只做记录和审计，不能单独触发交易。

## 新增安全机制

- 最少健康行情源数量：`MIN_MARKET_SOURCES`
- 报价最大允许年龄：`MAX_QUOTE_AGE_SECONDS`
- 价格使用中位数，降低单一异常源影响
- 任一关键数据不足时 fail-closed，只记录错误，不下单
- 记录失败源、过期源、价格离散度和资讯失败数
- 实盘仍然默认关闭，并继续阻止 SELL，直到完成真实持仓同步

示例配置：

```dotenv
RUN_MODE=paper
LIVE_ARMED=false
MIN_MARKET_SOURCES=3
MAX_QUOTE_AGE_SECONDS=30
MIN_SIGNAL_CONFIDENCE=0.70
```

## 运行

```bash
pip install -r requirements.txt
python main.py
```

首次及长期运行都建议使用 `RUN_MODE=paper`。多源数据不能保证准确或盈利；不同平台的交易对、稳定币价格、延迟和流动性不同，实际生产系统还应增加缓存、重试退避、限频、持久化、订单簿滑点估计、余额/持仓 reconciliation、监控告警和人工急停。
