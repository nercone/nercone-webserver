# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

[nercone.dev](https://nercone.dev/) のウェブサーバー本体のリポジトリ。FastAPI + Uvicorn で動く Python アプリケーションで、ポート 8080 でリッスンする。本番環境では Nginx がリバースプロキシ兼 TLS 終端として前段に立ち、GCP Compute Engine (AlmaLinux 10) 上の systemd サービスとして常駐している。

コンテンツ（HTML・Markdown・CSS・画像等）は別リポジトリ `website-contents` で管理されており、git submodule として `public/` ディレクトリにマウントされている。

## 2 つのリポジトリの関係

| リポジトリ | 役割 |
|---|---|
| `website`（本リポジトリ） | Python サーバー本体。ルーティング・レンダリング・ミドルウェアを担う |
| `website-contents` | ページ・アセット・テンプレート一式。`public/` に submodule として配置 |

`config.py` の `Directories.public` は `Path.cwd() / "public"` で解決される。したがって **サーバーは必ず `website/` をカレントディレクトリとして起動しなければならない**。別のディレクトリから起動すると `public/` が見つからずすべてのページが 404 になる。

## よく使うコマンド

```bash
# 依存関係のインストール（パッケージマネージャーは uv）
uv sync

# 開発サーバーを起動（website/ ディレクトリで実行すること）
uv run nercone-website
# または
uv run python -m nercone_website

# コンテンツ（submodule）だけを最新に更新
bash update-contents.sh
# 実質的に同じ: git submodule update --remote --merge public

# サーバー本体 + コンテンツを更新してサービス再起動（本番用）
bash update.sh
```

`update.sh` は①サービス停止 → ②`git pull --recurse-submodules` → ③submodule 更新 → ④`uv tool install` で再インストール → ⑤サービス再起動 という手順を踏む。

テストフレームワークは存在しない。動作確認には以下のエンドポイントを使う：

- `GET /ping` — "pong!" を返す死活確認
- `GET /status` — バージョン・日替わり名言・アクセスカウンターを JSON で返す
- `GET /welcome` — ASCII アートのウェルカム画面（テキスト）
- `GET /echo` — リクエストのログ情報を JSON で返す（信頼 IP からのみアクセス可）
- `GET /test/error-page/{status_code}` — 任意のエラーページを表示するテスト用エンドポイント

## アーキテクチャ

### ソースファイル一覧（`src/nercone_website/`）

```
__main__.py   uvicorn 起動エントリポイント。ログ設定もここで行う
server.py     FastAPI アプリ本体。全ルートを定義し、Jinja2 グローバルを登録する
middleware.py カスタム ASGI ミドルウェア。ホスト検証・サブドメインルーティング・minify・ヘッダー付与を担う
renderer.py   ページ解決とレンダリングのロジック（HTML / Markdown / 静的ファイル / ショートURL）
config.py     ディレクトリ定数・ファイル定数・ホスト名定数・IP 信頼判定・UserOptions
database.py   SQLite によるアクセスカウンター（databases/access_counter.db）
logger.py     JSON 形式のアクセスログ（logs/access.log）
proxy.py      HTTP / WebSocket リバースプロキシのファクトリ関数
```

### リクエスト処理フロー

1. **`Middleware.__call__`** がすべての HTTP / WebSocket リクエストを受け取る
2. **ホスト名検証**: `Hostnames.all`（`localhost`・`nercone.dev`・`nerc1.dev`・`diamondgotcat.net`・`d-g-c.net`・onion アドレス）に含まれないホスト名は 400 を返す。ただし信頼 IP（後述）からのアクセスはこの制限を受けない
3. **サブドメインルーティング**: サブドメインがある場合はドット区切りを逆順にしてパスに変換してアプリへ転送する（例: `foo.bar.nercone.dev/baz` → `/bar/foo/baz`）。4xx が返った場合は元のパスで再試行する。また末尾スラッシュありで 404 の場合はスラッシュを除去して再試行する
4. **minify**: レスポンスの Content-Type に応じて CSS（rcssmin）/ JavaScript（rjsmin）/ SVG（scour）をインラインで最適化する
5. **ヘッダー付与**: セキュリティヘッダー（CSP・Permissions-Policy・Referrer-Policy）・キャッシュヘッダー・`Server-Timing`・`Onion-Location` を付与して送信する

**信頼 IP** (`AccessSources.trusted`): RFC1918 プライベートアドレス・ループバック・リンクローカル・Tailscale CGNAT 帯域（100.64.0.0/10）が対象。信頼 IP からのリクエストはホスト名制限が免除され、`/echo` エンドポイントにもアクセスできる。

### ページ解決 (`renderer.py`)

`render()` は以下の順に解決を試みる：

1. **`resolve_page(path)`** — `public/` 以下を `.html` テンプレート優先、次に `.md` ファイルの順で検索する。パスに拡張子がない場合は `/index.html`・`/README.html`・`/index.md`・`/README.md` も候補に含む
2. **`resolve_file(path)`** — 静的ファイル（画像・フォント等）を `FileResponse` で返す。`public/` の外へのパストラバーサルは `PermissionError` で 403 を返す
3. **`resolve_shorturl(path)`** — `public/shorturls.json` を参照してリダイレクトまたはエイリアスを解決する（最大 10 段チェーン）
4. すべて失敗 → 404 エラーページ

**Markdown モード**: 以下のいずれかの条件を満たすリクエストには HTML ではなく `text/markdown` で応答する：
- User-Agent に `curl`・`claude-user`・`chatgpt-user`・`google-extended`・`perplexity-user` を含む
- `Accept: text/markdown` ヘッダーがある
- リクエストパスが `.md` で終わる

HTML ページの場合は Jinja2 でレンダリングしてから `<main>` 要素の内容を markitdown で Markdown に変換して返す。

**Markdown ページのレンダリング**: `.md` ファイルは mistune（カスタム `HTMLRenderer`）で HTML に変換する。コードブロックは `<pre>` のみで囲む（`<code>` なし）。Jinja2 テンプレート記法も本文中で使用できる。

**サムネイル生成** (`/assets/images/thumbnails/{path}`): クエリパラメータ `title`・`description`・`template`（`normal` or `error`）を受け取り、SVG テンプレート内の `__PATH__`・`__TITLE__`・`__DESCRIPTION__` を置換後、`resvg_py` で 1200×630 の PNG に変換して返す。

**Google Fonts CSS** (`/assets/css/google-fonts.css`): Google Fonts API から CSS を取得してインメモリで 24 時間キャッシュする。

### コンテンツ構造（`website-contents` / `public/`）

**テンプレートシステム**: すべての HTML ページは Jinja2 テンプレートで、`base.html` を extend する。

```html
{% extends "/base.html" %}
{% block title %}ページタイトル{% endblock %}
{% block description %}説明{% endblock %}
{% block main %}...{% endblock %}
```

**Markdown ページの YAML frontmatter**: frontmatter のキーが Jinja2 の `{% block <key> %}` に自動マッピングされる。

```markdown
---
title: ページタイトル
header_title_prefix: About
description: 説明文
---
本文（Jinja2 テンプレート記法も使用可）
```

**Jinja2 グローバル変数・フィルター**:

| 名前 | 種別 | 内容 |
|---|---|---|
| `server_version` | 変数 | サーバーリポジトリの git 短縮ハッシュ |
| `contents_version` | 変数 | コンテンツリポジトリの git 短縮ハッシュ |
| `onion_site_url` | 変数 | Tor onion サイトの URL |
| `get_access_count()` | 関数 | 累積アクセスカウンターの値 |
| `get_daily_quote()` | 関数 | `public/quotes.txt` からその日のランダムな名言（日付シード）|
| `this_year()` | 関数 | 日本時間での現在の西暦年 |
| `this_year_in_heisei()` | 関数 | 現在の平成換算年（`西暦 - 1988`） |
| `re_sub` | フィルター | `re.sub(pattern, repl, s)` のラッパー |

**ショートURL** (`shorturls.json`): `redirect` 型（外部 URL への 307 転送）と `alias` 型（別キーへの参照）の 2 種類がある。

### フロントエンド JS

| ファイル | 役割 |
|---|---|
| `view-transition.js` | View Transition API を使った SPA ライクなページ遷移。`<header>` / `<main>` / `<footer>` だけを差し替え、スクリプトも再実行する |
| `class-prefix.js` | レスポンシブ CSS プレフィックスシステム。`small:` / `medium:` / `large:` クラスをブレークポイントに応じてトグルする（≤740px / 741–1080px / ≥1081px） |
| `cursor.js` | カスタムカーソル実装 |
| `loading-overlay.js` | ページ遷移中のオーバーレイ |

`view-transition.js` はページ遷移後にカーソル（`__cursorCleanup` / `__cursorReinit`）と `class-prefix.js`（`__classPrefixReinit`）を再初期化するフックを持つ。

### CSS 構成

- `colors.css` — CSS カスタムプロパティとユーティリティクラス（`text-*` / `bg-*` / `border-*`）
- `main.css` — レイアウト・コンポーネント（`.flex` / `.block` / `.hide` / `.show` など）
- `fonts.css` — フォントファミリーユーティリティ。Google Fonts は `assets.nercone.dev` の CDN 経由でプロキシされる
- `themes/dark.css` / `themes/light.css` — `--color-theme-*` CSS 変数定義
- `pages/*.css` — ページ固有スタイル

### デプロイ構成

| ファイル | 説明 |
|---|---|
| `nercone-website.service` | サーバーの systemd サービス。WorkingDirectory は `/srv/website`、エントリポイントは `/root/.local/bin/nercone-website` |
| `nercone-website-autoupdater.service` | `update.sh` を実行する oneshot サービス |
| `nercone-website-autoupdater.timer` | 毎日 00:00 UTC に autoupdater を起動するタイマー |

パッケージ管理は `uv tool install` で行われ、エントリポイント `nercone-website` が `/root/.local/bin/` に配置される。ログは `logs/` 以下に、SQLite データベースは `databases/` 以下に置かれる。いずれも `website/` を起点とした相対パスで解決される。

---

Writed by **Claude Code (Model: Sonnet 4.6)** at **Tue May 12 14:12:21 JST 2026**.
