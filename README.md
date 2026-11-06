# Market Dashboard

**网站：https://yeohkj-dev.github.io/c9-dashboard/**

手机可用的美股市场仪表板：指数、市场宽度（新高/新低、涨跌家数、Weinstein Stage 1–4）、主题 ETF 追踪、Stage 2 新高股。

> **给 Claude：** 接手前先读 [CLAUDE.md](CLAUDE.md)（完整交接说明：架构、规则、检查方法、踩过的坑、用户偏好）。

## 自动运行

全部在 GitHub Actions 上跑，**不需要开电脑，也不依赖 Claude 账号**。

- **数据更新**（`update.yml`）：周一至五，马来西亚时间 20:00（开盘前）、22:15–04:15 每小时、05:30（收盘后）。
- **防停用**（`keepalive.yml`）：每月 1 号自动做一次空 commit。GitHub 会停用 60 天没有活动的仓库的定时任务，这个可以避免。
- 想马上更新：[Actions](https://github.com/yeohkj-dev/c9-dashboard/actions) → Update dashboard → Run workflow。

如果收到 GitHub 邮件说 workflow 被停用：到 Actions 页面，点该 workflow，再点 **Enable workflow**。

## 加到手机主屏幕

- iPhone（Safari）：分享 → 添加到主屏幕
- Android（Chrome）：⋮ → 添加到主屏幕 / 安装应用

## 以后要改东西

跟 Claude 说：「去看 https://github.com/yeohkj-dev/c9-dashboard ，我要改……」。Claude 会先读 CLAUDE.md 再继续。

常见修改位置：

- 主题 ETF：`update_data.py` 里的 `THEMES`
- 更新时间：`.github/workflows/update.yml` 的 `cron`（UTC，马来西亚 = UTC + 8），同时改 `site/index.html` 的 `RUNS_UTC`
- 股票池：`tickers.csv`

## 本地测试

```bash
pip install -r requirements.txt
python update_data.py
python -m http.server 8765 --directory site
```
