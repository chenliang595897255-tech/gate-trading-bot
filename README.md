# Gate.io Trading Bot

这是一个 Gate.io 现货自动交易机器人示例。

> 本项目不会保存或上传你的 Gate.io 登录密码。机器人使用 API Key 和 API Secret 访问账户；请勿开启提现权限，也不要把真实密钥提交到 GitHub。

默认策略：

- 5 分钟 K 线
- 5 周期与 20 周期均线交叉
- 金叉买入
- 死叉卖出
- 支持止损和止盈
- 支持每日亏损熔断
- 默认 `DRY_RUN=true`，不会真实下单

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows：

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 配置 Gate.io API

1. 登录 Gate.io 官方网站。
2. 打开 **账户设置 → API 管理**。
3. 创建 API Key。
4. 只开启读取和现货交易权限。
5. **关闭提现权限**，并尽量绑定固定 IP。
6. 复制 API Key 和 API Secret；不要使用 Gate.io 登录密码。

复制配置模板：

```bash
cp .env.example .env
```

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

编辑 `.env`，将下面两项替换成你自己的值：

```dotenv
GATE_API_KEY=在这里填写你的Gate_API_Key
GATE_API_SECRET=在这里填写你的Gate_API_Secret
```

`.env` 已加入 `.gitignore`，不会被 Git 提交。不要在聊天、截图、Issue 或代码中公开 API Secret。

## 运行模拟模式

确认 `.env` 中保持：

```dotenv
DRY_RUN=true
```

然后运行：

```bash
python main.py
```

模拟模式只读取行情并在本地模拟仓位，不会真实下单。

## 开启实盘

只有完成回测、模拟运行和小额验证后，才考虑修改：

```dotenv
DRY_RUN=false
```

实盘前请再次确认 API Key 没有提现权限，且 `ORDER_USDT`、`MAX_POSITION_USDT` 和 `MAX_DAILY_LOSS_USDT` 设置得足够小。

## 注意事项

这个项目不是盈利保证，也没有实现：

- 真实交易所持仓同步
- 已成交订单确认
- 部分成交处理
- 精确的交易手续费计算
- 交易对最小数量和价格精度自动读取
- 断线后的状态恢复
- 多进程锁
- Web 监控面板

正式实盘前必须继续完善这些功能。
