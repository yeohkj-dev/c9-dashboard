# C9 Market Dashboard

手机可用的美股市场仪表板：指数、市场宽度（新高/新低、涨跌家数、Weinstein Stage 1–4）、主题 ETF 追踪、Stage 2 新高股。
GitHub Actions 定时抓取 Yahoo Finance 数据并发布到 GitHub Pages，电脑关机也会更新。

## 文件

| 文件 | 用途 |
|---|---|
| `update_data.py` | 抓数据，生成 `site/data.json` |
| `tickers.csv` | 市场宽度用的股票池（S&P 500 + 400 + 600） |
| `site/index.html` | 手机网页 |
| `.github/workflows/update.yml` | 定时任务：周一至五，美股开盘前、交易时段每小时、收盘后 |

## 第一次上线（只需做一次）

1. 在 https://github.com/new 建一个 **Public** 的 repo，例如 `c9-dashboard`（不要勾选 README）。
2. 在这个文件夹打开终端，执行（把 `你的用户名` 换掉）：
   ```bash
   git remote add origin https://github.com/你的用户名/c9-dashboard.git
   git push -u origin main
   ```
   第一次 push 会弹出浏览器让你登录 GitHub。
3. repo 页面 → **Settings → Pages → Build and deployment → Source** 选 **GitHub Actions**。
4. **Actions** 页 → 左边选 **Update dashboard** → **Run workflow**，等约 2 分钟。
5. 网址：`https://你的用户名.github.io/c9-dashboard/`

## 加到手机主屏幕

- iPhone（Safari）：分享 → 添加到主屏幕
- Android（Chrome）：⋮ → 添加到主屏幕 / 安装应用

## 本地测试

```bash
pip install -r requirements.txt
python update_data.py
python -m http.server 8765 --directory site
```

## 修改

- 主题 ETF：改 `update_data.py` 里的 `THEMES`。
- 更新时间：改 `update.yml` 里的 `cron`（UTC 时间，马来西亚时间 = UTC + 8）。
- 股票池：改 `tickers.csv`。
