# 交接说明（给接手的 Claude）

> 用户以后可能只会说「去看 https://github.com/yeohkj-dev/c9-dashboard」。**先读完这份文件再动手。**
> 这个项目完全跑在 GitHub 上，不依赖任何 Claude 账号，也不依赖用户的电脑。

## 1. 这是什么

手机用的美股市场仪表板（Market Dashboard），风格参考用户提供的截图，理念来自用户上过的「C9 / 平凡师奶 图表技术分析课程」（Weinstein 四阶段、Minervini VCP、只做 Stage 2 强势股）。

- 网站：https://yeohkj-dev.github.io/c9-dashboard/
- 仓库：https://github.com/yeohkj-dev/c9-dashboard （Public，免费版 Pages 只能用于公开 repo）
- 用户本地副本：`D:\AI\Claude AI\c9 training\dashboard`（可能不存在于新电脑；需要时 `git clone`）

页面内容：

| 区块 | 内容 |
|---|---|
| Indexes | SPY / QQQ / IWM 价格、涨跌，盘前 ☀ / 盘后 ☾ 涨跌幅 |
| Market Breadth | S&P 1500 的 52 周新高 vs 新低、上涨 vs 下跌家数、Stage 1–4 分布、股价在 50 / 200 天线上的比例 |
| Theme Tracker | 31 个主题 ETF，Today / 1W / 1M / YTD 排序 |
| Stage 2 新高股 | Stage 2 且创 52 周新高的股票，按今日涨幅取前 20，点击开 TradingView |

## 2. 怎么运作

```
GitHub Actions (update.yml, 定时)
  → pip install -r requirements.txt
  → python update_data.py   # 从 Yahoo Finance 抓数据，写 site/data.json
  → upload-pages-artifact(site/) → deploy-pages
用户手机打开网站 → index.html 读取 data.json 渲染
```

- `site/data.json` **不进 git**（在 .gitignore），每次都在 Actions 里重新生成，直接部署到 Pages。
- Pages 的 Source 必须是 **GitHub Actions**（Settings → Pages）。

## 3. 文件

| 文件 | 用途 |
|---|---|
| `update_data.py` | 抓数据并计算。`THEMES` = 主题→ETF 对照；`INDEXES`；Stage 规则常量 `MA_LEN / SLOPE_DAYS / FLAT_PCT` |
| `tickers.csv` | 市场宽度股票池：S&P 500 + 400 + 600（约 1,500 只，2026-10-27 从 Wikipedia 抓取）。成分股会变，偶尔要重抓 |
| `requirements.txt` | `yfinance>=1.7`（旧版会被 Yahoo 拦截，报 rate limited）、pandas |
| `site/index.html` | 单页网页（纯 HTML/CSS/JS，无框架），深色，手机优先 |
| `site/manifest.json`、`site/icon-*.png` | 「添加到主屏幕」用 |
| `.github/workflows/update.yml` | 定时更新 + 部署 |
| `.github/workflows/keepalive.yml` | 每月 1 号空 commit，防止 GitHub 因 60 天无活动停用定时任务。改动这个文件并 push 也会跑一次（方便测试，用户手机上找不到 Run workflow 按钮）。它用 GITHUB_TOKEN 推送，不会再触发 update.yml |
| `README.md` | 给用户看的简短说明 |

## 4. 更新时间（update.yml，UTC，周一至五）

| cron (UTC) | 马来西亚时间 | 用途 |
|---|---|---|
| `0 12 * * 1-5` | 20:00 | 开盘前 |
| `15 14-20 * * 1-5` | 22:15 – 04:15 每小时 | 交易时段 |
| `30 21 * * 1-5` | 05:30 | 收盘后 |
| push 到 main | 立即 | 改代码后马上部署 |
| workflow_dispatch | 手动 | Actions 页面的 Run workflow |

GitHub 的定时任务常延迟 5–40 分钟，属正常。`site/index.html` 里的 `RUNS_UTC` 要和这里的 cron 保持一致（用来显示「下次自动更新」）。

## 5. 关键规则

**Stage（Weinstein）**：用 150 天均线（≈30 周线），斜率 = 现在 vs 20 天前，变化超过 ±1% 才算上升/下降。
- 股价 > 均线 且 均线上升 → Stage 2
- 股价 < 均线 且 均线下降 → Stage 4
- 股价 > 均线，均线走平或下降 → Stage 1
- 股价 < 均线，均线走平或上升 → Stage 3

**新高/新低**：当天 High ≥ 过去 252 天最高 / 当天 Low ≤ 过去 252 天最低。

**容错**：`download()` 失败会重试最多 4 次；某一区块仍失败时，从线上 `data.json` 沿用上次数据，并写入 `stale` 字段，页面会显示「××沿用上次数据」。三个区块全失败才让这次运行失败（线上保持旧版）。

## 6. 用户偏好（跟用户沟通时）

- 用中文沟通；成品输出给本地 HTML 文件。
- 改网页外观前，先本地预览给用户看，用户同意再 push（push 会直接上线）。
- 用户不是工程师：GitHub 网页上的操作要给具体点击路径。
- 用户用浏览器登录 GitHub 推送（Git Credential Manager），电脑没有 `gh` CLI。

## 7. 怎么检查是否正常

不需要登录（公开 repo）：

```bash
# 最近的运行结果
curl -s "https://api.github.com/repos/yeohkj-dev/c9-dashboard/actions/runs?per_page=10"
# 线上数据时间、是否有沿用旧数据
curl -s "https://yeohkj-dev.github.io/c9-dashboard/data.json"
# 失败的运行：看哪一步失败（完整 log 需要登录）
curl -s "https://api.github.com/repos/yeohkj-dev/c9-dashboard/actions/runs/<RUN_ID>/jobs"
```

本地测试：

```bash
pip install -r requirements.txt
python update_data.py
python -m http.server 8765 --directory site
```

## 8. 踩过的坑

- yfinance 0.2.x 会被 Yahoo 拦截 → 已改用 ≥1.7。
- 2026-10 曾有约 2/5 的运行因 Yahoo 偶发返回空数据而失败 → 加了重试 + 沿用上次数据，之后 60 次运行全部成功。
- 原本 push 不会触发部署，改了网页要等下一次定时任务才上线 → 已加 `push` 触发。
- 浏览器 / Pages 有缓存（最多约 10 分钟）；手机看到旧画面时下拉重新载入。
- 用户的 3 张参考截图（`*.jpg`）在 .gitignore，不要上传。
- GitHub 的 Node 20 弃用警告：actions 已升到 checkout@v5、setup-python@v6、upload-pages-artifact@v4。

## 9. 修改记录

- 2026-10-27：建立。指数、宽度、Stage、主题、Stage 2 新高股；GitHub Actions + Pages。
- 2026-10-28：标题改为 MARKET DASHBOARD；刷新按钮提示 + 下次更新时间；下载重试与沿用上次数据；push 触发部署。
- 2026-11-06：加 keepalive.yml；加这份交接说明。keepalive 改为「自身文件改动时也运行」，用来测试。

## 10. 可能的后续（用户尚未要求）

- 马股（Bursa）版本。
- 扩大股票池到全美股（截图约 5,600 只）。
- Telegram 推送（用户另一个项目 jlaw-daily-report 已有做法，可参考）。
