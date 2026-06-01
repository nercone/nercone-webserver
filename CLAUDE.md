# CLAUDE.md
このファイルは、Claude Codeがこのリポジトリ内のコードを扱う際に知っておくべき情報を提供するものです。

## 概要
ここは[nercone.dev](https://nercone.dev/)のWebサーバー本体のソースコードを管理しているリポジトリです。

Python 3.12のFastAPI + Uvicornの上で動くASGIアプリケーションです。Uvicornは`workers=4`で起動し、UDS(`WEBSITE_UDS`環境変数が設定されている場合)またはTCP(`0.0.0.0:8080`)でリッスンします。

コンテナ環境ではNginxがリバースプロキシとして前段に存在し、UDSを通じてアプリに接続します。

## 関連リポジトリ

- `website` (`https://github.com/nercone-dev/website/`)
- `website-contents` (`https://github.com/nercone-dev/website-contents/`)

コンテンツ (HTML、Markdown、CSS、画像など) は別リポジトリ`website-contents`で管理されており、`git submodule`を使用し`public/`ディレクトリにマウントされています。

アクセスカウンタなどの一部の例外を除き、外部からのアクセスに対して`public/`ディレクトリ外のファイルのコンテンツに関する情報、またはそれを予測できるような情報は、リクエストに少しも含めてはなりません。
これはセキュリティ上最も重要と言えます。そのため、このルールに従わない手法での機能の実装方法や問題の解決策は考えるべきではありません。

## ファイル構造

### `website` (`/`)

```
https://github.com/nercone-dev/website.git
├── databases
│   ├── .gitkeep
│   ├── access_counter.txt       # アクセスカウンタ (整数テキスト)
│   └── mime.types               # Apache httpd から30日毎に自動取得するMIMEタイプ定義
├── logs
│   ├── .gitkeep
│   ├── app.log                  # 一般ログ (Logger.log)
│   ├── access.log               # アクセスログ (JSONL形式)
│   └── error.log                # 5XXエラー時のPythonトレースバック
├── src
│   └── nercone_website
│       ├── __init__.py
│       ├── __main__.py          # エントリポイント・Uvicorn起動
│       ├── constants.py         # 定数・パス・ホスト名定義
│       ├── logger.py            # ロギング (Logger クラス)
│       ├── databases.py         # MimeTypes・AccessCounter
│       ├── manager.py           # PPManager・CSPManager・TimingManager・NetworkManager・OptionManager
│       ├── resolver.py          # ファイル・ページ・ショートURL解決
│       ├── templates.py         # Jinja2テンプレート環境・デイリークォート
│       ├── app.py               # FastAPIアプリ・ルーティング定義
│       ├── renderer.py          # レスポンス生成・Markdown/HTML変換・サムネイル生成
│       └── middleware.py        # ASGIミドルウェア・minify・セキュリティヘッダー付与・ロギング
├── public -> https://github.com/nercone-dev/website-contents.git
├── .gitignore
├── .gitmodules
├── README.md
├── CLAUDE.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── docker-compose.yml
├── update.sh
└── update-contents.sh
```

### `website-contents` (`/public/`)

```
https://github.com/nercone-dev/website-contents.git
├── .well-known
│   ├── openpgpkey
│   │   ├── hu
│   │   │   ├── mdufcioqzud8czcx79fo1zq1ytp1gggk
│   │   │   └── oonafwamehuud1q4eb4qkd8gfnxyjohn
│   │   ├── nercone.dev
│   │   │   ├── hu
│   │   │   │   ├── mdufcioqzud8czcx79fo1zq1ytp1gggk
│   │   │   │   └── oonafwamehuud1q4eb4qkd8gfnxyjohn
│   │   │   └── policy
│   │   └── policy
│   └── security.txt
├── assets
│   ├── images
│   │   ├── dotcat
│   │   │   ├── 2nd
│   │   │   │   └── ...
│   │   │   ├── error
│   │   │   │   └── ...
│   │   │   ├── forks
│   │   │   │   └── ...
│   │   │   ├── labs
│   │   │   │   └── ...
│   │   │   ├── os
│   │   │   │   └── ...
│   │   │   ├── step
│   │   │   │   └── ...
│   │   │   └── ...
│   │   ├── dotgirl
│   │   │   └── ...
│   │   ├── thumbnail
│   │   │   ├── template         # サムネイル生成用SVGテンプレート (例: normal.svg)
│   │   │   │   └── ...
│   │   │   └── ...
│   │   ├── symbol
│   │   │   ├── extended
│   │   │   │   └── ...
│   │   │   └── ...
│   │   ├── header
│   │   │   └── ...
│   │   ├── wallpaper
│   │   │   └── ...
│   │   ├── 3rd-party
│   │   │   └── ...
│   │   ├── other
│   │   │   └── ...
│   │   └── ...
│   ├── fonts
│   │   └── ...                  # NerconeSansJP / NerconeMonoJP (TTF, サムネイル生成に使用)
│   ├── css
│   │   ├── pages
│   │   │   ├── color-palette.css
│   │   │   ├── daily-quote.css
│   │   │   ├── index.css
│   │   │   ├── links.css
│   │   │   ├── qr-code.css
│   │   │   └── sidebar.css
│   │   ├── themes
│   │   │   ├── dark.css
│   │   │   └── light.css
│   │   ├── main.css
│   │   ├── fonts.css
│   │   ├── colors.css
│   │   ├── cursor.css
│   │   ├── components.css
│   │   ├── layout.css
│   │   ├── miscellaneous.css
│   │   ├── view-transition.css
│   │   └── loading-overlay.css
│   ├── js
│   │   ├── pages
│   │   │   └── index.js
│   │   ├── main.js
│   │   ├── components.js
│   │   ├── cursor.js
│   │   ├── view-transition.js
│   │   ├── loading-overlay.js
│   │   └── class-prefix.js
│   └── pgp
│       ├── nenaicone.asc
│       └── nercone.asc
├── about
│   ├── index.md
│   └── server.md
├── error
│   ├── client.md                # クライアントエラー (4XX) 用テンプレート
│   ├── server.html              # 5XXエラー用テンプレート (レンダリングなし・そのまま返却)
│   └── nginx.html               # 502/503/504エラー用テンプレート (レンダリングなし)
├── test
│   ├── html.html
│   ├── markdown.md
│   ├── font-size.md
├── base                         # 基底テンプレート (Jinja2 extends)
│   ├── normal.html
│   └── sidebar.html
├── index.html
├── links.html
├── download-banner.md
├── projects.html
├── public-key.html
├── color-palette.md
├── daily-quote.html
├── access-counter.md
├── credit.md
├── options.md
├── qr-code.html
├── vulnerability-reporters.md
├── sitemap.xml
├── quotes.txt                   # デイリークォートの候補一覧 (1行1エントリ)
├── robots.txt
├── shorturls.json               # ショートURL定義 (redirect / alias の2種類)
└── site.webmanifest
```

## モジュール詳細

### `constants.py`
グローバルな定数・パス定義。アプリ起動時に一度だけ評価される。

- `Directories`: `base`(CWD)、`public`、`logs`、`databases`の`Path`オブジェクト
- `Files`: `mime.types`、`access_counter.txt`、各ログファイルの `Path`
- `Repositories`: 起動時に`git rev-parse --short HEAD`でコミットハッシュを取得 (`Server.version`、`Contents.version`)
- `Hostnames`: 許可ホスト名リスト(`www`/`tor`/`local`/`public = www + tor`/`all = local + public`)
- `unix_socket`: `WEBSITE_UDS`環境変数の値 (未設定の場合は `None`)

### `databases.py`
永続データの読み書き。

- `MimeTypes`: Apache httpdの`mime.types`をHTTP/2で取得し`mimetypes`モジュールに登録する。30日でキャッシュ切れ、起動時 (`__main__`) に1回フェッチし、アプリ初期化 (`app.py`) 時にロードする。
- `AccessCounter`: `databases/access_counter.txt`への排他ロック(`fcntl.LOCK_EX`)を使ったカウンタ。`get()`で読み取り、`increase()`でインクリメント。

### `logger.py`
ファイルへの排他ロック書き込みロガー。

- `Logger.log()`: `logs/app.log`への一般ログ書き込み
- `Logger.log_access()`: `logs/access.log`へのJSONL形式アクセスログ。リクエストID/URL/ステータス/メソッド/クライアント情報/全リクエスト/レスポンスヘッダー/PPManager/CSPManager/TimingManagerの状態を記録する。
- `Logger.log_error()`: `logs/error.log`へのトレースバック記録

### `manager.py`
リクエストスコープにアタッチされる各種マネージャー。`Middleware.__call__` でインスタンス化され `scope` に格納される。

- `PPManager`: `Permissions-Policy`ヘッダーを管理。`set()`/`append()`/`remove()`で操作し`header`プロパティでヘッダー文字列化。
- `CSPManager`: `Content-Security-Policy`ヘッダーを管理。`set()`/`append()`/`remove()`で操作し`header`プロパティでヘッダー文字列化。
- `TimingManager`: `Server-Timing`ヘッダー用の処理時間計測。`start(key)`/`stop(key)`でスパンを記録し`header`プロパティで出力。(計測対象: `total`/`recieve`/`app`/`app-retry`/`resolve-page`/`resolve-shorturl`/`render`/`convert`/`etag`/`minify`)
- `NetworkManager`: クライアントのIPアドレス情報を保持。UDS接続時は `X-Real-IP` ヘッダーからホストを取得。`trusted`プロパティでプライベートIP帯(RFC 1918/RFC 6890等)か判定。
- `OptionManager`: クエリパラメータとCookieを統合してユーザーオプションを管理。クエリパラメータは`apply()`呼び出し時に自動でCookieに永続化される(`.once`サフィックスを持つキーは永続化されない)。

### `resolver.py`
リクエストパスを実際のファイルに解決するロジック。

- `resolve_file(path)`: `public/`配下のファイルを返す。`Path.resolve()` + `is_relative_to()`でディレクトリトラバーサルを防止。存在しない場合は `None`、トラバーサルは `PermissionError`。
- `resolve_page(path, markdown_mode)`: HTMLファイルとMarkdownファイルの候補を優先順位順に探索する。`markdown_mode=True`の場合は`.md`を優先して検索する。
- `resolve_shorturl(path)`: `shorturls.json`を読んで短縮URL(`redirect` または `alias`)を解決する。`alias`はチェーン解決可能で最大10回まで(循環検出あり)。

### `templates.py`
Jinja2テンプレート環境の初期化とテンプレートグローバル関数の定義。

- `templates`: `Jinja2Templates(directory=public/)` で初期化。フィルタ`re_sub`を追加。
- グローバル変数: `access_counter`/`Repositories`/`Hostnames`
- グローバル関数: `this_year()`/`this_year_in_heisei()`/`get_daily_quote()`
- `get_daily_quote()`: `quotes.txt`から日付をシードにして1日1エントリを返す (UTCの日付でシード)。

### `renderer.py`
HTTPレスポンスの生成ロジック。

- `CustomHTMLRenderer`: `mistune`のカスタムレンダラー。`block_code`でコードブロックのシンタックスハイライトを無効化、`block_quote`でアラート記法(`[!NOTE]`/`[!WARNING]`等)を`div.block-{type}`に変換する。
- `htmlitdown`: `mistune`インスタンス。プラグイン: `table`/`strikethrough`/`task_lists`/`footnotes`。
- `markitdown`: `MarkItDown()`インスタンス (HTML -> Markdownのリバース変換用)。
- `default_response(path, request, ...)`: メインのレスポンス生成関数。処理順序:
  1. `resolve_page`でページファイルを探索
  2. YAMLフロントマター(`---` ブロック)を解析して`base`/各ブロックを設定
  3. Jinja2でレンダリング後、HTMLまたはMarkdownを生成
  4. `markdown_mode`時は`BeautifulSoup`で`<main>`を抽出し`markitdown`でMarkdown変換
  5. SHA-256でETagを計算、`If-None-Match`と一致すれば304を返す
  6. ページ未発見 -> `resolve_file` -> `resolve_shorturl` の順でフォールバック
- `render_error_page(request, status_code, ...)`: エラーレスポンスの生成。502/503/504は`error/nginx.html`、他の5XXは`error/server.html`をレンダリングなしで返す。4XXは`error/client.md`をコンテキスト付きでレンダリングする。
- `render_thumbnail_png(path, title, description, template)`: SVGテンプレートの`__PATH__`/`__TITLE__`/`__DESCRIPTION__` を置換後、`resvg_py`で1280×640のPNGに変換する。フォントは`public/assets/fonts/`の NerconeSansJP/NerconeMonoJPを使用。

#### `markdown_mode` の判定ロジック (`renderer.py:46-47`)
以下のいずれかに該当する場合に`markdown_mode = True`となる:
- パスが `.md` で終わる
- `Accept` ヘッダーに `text/markdown` が含まれる
- `User-Agent` ヘッダーに `curl`/`claude-user`/`chatgpt-user`/`google-extended`/`perplexity-user` のいずれかが含まれる (AIクローラー向けに生のMarkdownを返す)

### `middleware.py`
ASGI形式のミドルウェア(`Middleware` クラス)。FastAPIの`add_middleware`ではなくStarletteの低レベルASGI形式で実装されており、レスポンスボディを一括取得した後に後処理を行える。

**リクエスト処理フロー:**
1. `scope["type"]`が`http`/`websocket`以外は素通り
2. `scope` に各マネージャー(`id`/`pp`/`csp`/`timings`/`network`/`options`)を注入
3. `timings.start("total")`
4. ホスト名チェック: 不正なホスト名は403 (trusted networkからのアクセスは除外)
5. WebSocket はサブドメインパス変換のみ行い素通り
6. OPTIONSリクエストは204を返して終了
7. リクエストボディを一括読み取り (`read_body`)
8. サブドメイン処理: `""` / `"www"` 以外のサブドメインはパスに変換 (例: `foo.nercone.dev/bar` -> `/foo/bar`)。サブドメインパスで4XX が返った場合は元のパスでリトライ(`app-retry`)。
9. `send()` でレスポンスを後処理してから送信

**`send()` の後処理:**
- `text/html` -> `minify_html.minify` (JS/CSSのインラインminifyも有効)
- `text/css` -> `rcssmin.cssmin`
- `text/javascript` / `application/javascript` -> `rjsmin.jsmin`
- `image/svg` -> `scour` (SVG最適化: ID短縮/コメント除去/改行除去)
- レスポンスヘッダー付与: `Content-Length`/`X-Request-Id`/`Server`/`Onion-Location`/`Link`/`Cache-Control`/`Referrer-Policy`/`Permissions-Policy`/`Content-Security-Policy`/`Access-Control-*`
- `Server-Timing` を最後に付与 (stop("total") の後)
- `Logger.log_access()` でアクセスログを記録

### `app.py`
FastAPIルーティング定義。`docs_url=None`/`redoc_url=None`/`openapi_url=None` でOpenAPI/Swagger UIは無効。

## エンドポイント一覧

| パス | メソッド | 説明 |
|------|----------|------|
| `/ping` | GET | ヘルスチェック。`pong!`を返す。 |
| `/welcome` | GET | ASCIIアートのウェルカムメッセージ + バージョン情報。 |
| `/status` | GET | JSON形式のステータス。`status`/`version`(server/content)/`quote`(デイリークォート)/`counter`(アクセス数)を含む。 |
| `/assets/images/thumbnail/template/{template}` | GET | サムネイルPNG生成。クエリ: `path`/`title`/`description`。 |
| `/error/{status_code}` | GET | エラーページのプレビュー。`server`/`nginx`またはHTTPステータスコードを指定。 |
| `/{path:path}` | GET/POST/HEAD | メインルート。`resolve_page` -> `resolve_file` -> `resolve_shorturl` の順でレスポンスを決定。 |

## 設定と起動

### 環境変数
- `WEBSITE_UDS`: Unix Domain Socket のパス。設定されている場合はUDSでリッスン(Nginxとの連携用)。未設定の場合は`0.0.0.0:8080`でTCPリッスン。

### 起動コマンド
```sh
# 開発時 (TCP)
uv run nercone-website

# 本番 (Docker Compose)
docker compose up -d
```

### Docker構成
- `docker-compose.yml`で`network_mode: host`を使用
- UDSソケットは`/run/website/app.sock`にマウント
- `logs/`/`databases/`はバインドマウントで永続化
- `public/`は読み取り専用でマウント (`:ro`)
- `.git/`も読み取り専用でマウント (バージョン情報取得用)

## コンテンツレンダリング仕様

### フロントマター
HTMLファイルとMarkdownファイルの先頭に `---` で囲まれたYAML形式のフロントマターを記述できる。

```yaml
---
base: normal       # 継承するベーステンプレート (デフォルト: normal, /base/normal.html)
title: ページタイトル   # テンプレートのtitleブロックを上書き
description: 説明文    # その他のブロックも任意に指定可能
---
```

フロントマターが設定されている場合、`{% extends "..." %}` と各 `{% block %}` が自動生成され、Jinja2でレンダリングされる。

### テンプレート変数
Jinja2テンプレート内で利用可能なグローバル変数/関数:

- `request`: Starletteの`Request`オブジェクト
- `access_counter`: `AccessCounter`インスタンス (`.get()`でカウント値取得)
- `Repositories`: `Server.version`/`Contents.version`/`Server.url`/`Contents.url`
- `Hostnames`: `www`/`tor`/`local`/`public`/`all`
- `this_year()`: 日本時間の現在年
- `this_year_in_heisei()`: 平成換算の現在年 (year - 1988)
- `get_daily_quote()`: デイリークォート文字列
- フィルタ `re_sub(pattern, repl)`: 正規表現置換

### 短縮URL (`shorturls.json`)

```json
{
  "short-key": {"type": "redirect", "content": "https://..."},
  "alias-key": {"type": "alias", "content": "other-short-key"}
}
```

- `redirect` — 307リダイレクト
- `alias` — 別のキーにフォールバック (最大10チェーン、循環検出あり)

## 依存関係

| パッケージ | 用途 |
|-----------|------|
| `fastapi` | WebフレームワークとルーティングAPI |
| `uvicorn[standard]` | ASGIサーバー |
| `jinja2` | HTMLテンプレートエンジン |
| `mistune` | Markdown -> HTML変換 |
| `markitdown` | HTML -> Markdown変換 (CLIツール/AIクローラー向けレスポンス用) |
| `beautifulsoup4` | HTML解析 (markdown_modeで`<main>`要素抽出) |
| `resvg-py` | SVG -> PNG変換 (サムネイル生成) |
| `scour` | SVGの最適化/最小化 |
| `rjsmin` | JavaScriptの最小化 |
| `rcssmin` | CSSの最小化 |
| `minify-html` | HTMLの最小化 (JS/CSSインラインも対象) |
| `httpx[http2]` | HTTP/2クライアント (mime.typesのフェッチ) |
| `websockets` | WebSocketサポート |
| `fourword` | [FourWord ID](https://github.com/nercone-dev/fourword/)の生成 |
| `pyyaml` | フロントマターのYAML解析 |

## Claudeによるコミット
コードやコンテンツに変更を加える場合、次を遵守してください。

- 可能な限り既存のコードのスタイルや構造を維持し、その上でシンプルな方法を用いて機能の実装や問題の解決を行い、可読性の高いコードで実装してください。
- 各機能/モジュールは他の機能/モジュールや共通部分に、その機能/モジュール専用のコードを含めないように努力してください。追加する以外の方法が全く存在しない場合、追加されるコードを最低限に抑えてください。
- 安全性や信頼性に少しでも影響がある場合、可能な限り慎重に実装方法を検討してください。
- 人間が変更内容を誤解なく完全な状態で理解できる必要があります。作業中に中程度の頻度で詳細な作業ログを目立つ形で提供してください。

人間によるレビューで承認され、人間によりコミットの作成が要求された場合、次を遵守した上でコミットを作成することができます。

- 実際にコミットを作成する前に、作成する際に使用するコミットメッセージや、コミットに含める(つまり、`git add`でステージングする)変更を詳細にまとめ、人間に伝え、承認され次第コミットを作成してください。
- コミットメッセージは日本語で書いてください。
- コミットメッセージの終盤に英語への翻訳も記載してください。
- コミットメッセージの1行目のテキストは、コミットの内容や2行目以降の内容を知らない場合でも簡単にコミットの内容を理解できるものにしてください。
- コミットメッセージの2/3行目以降で、より詳細な変更内容をまとめてください。
- コミットメッセージの1行目に`Claude: `プレフィックスを付けてください。
- `Assisted-by: AGENT_NAME:MODEL_VERSION [TOOL 0] [TOOL 1]`の形式のトレーラーをコミットに含ませてください。
    - `AGENT_NAME`には`Claude`/`ChatGPT`/`Gemini`のような名称を使用してください。
    - `MODEL_VERSION`には`claude-sonnet-4.6`のようなテキストを使用してください。
    - `[TOOL 0] [TOOL 1]`の部分は、コードを分析するのに使用したツールの名称を空白区切りで記載してください。
        - gitやuv、clangなどの日常的に使用される基本的なツールについては、記載する必要はありません。

## 補足
- `/status`エンドポイントのレスポンスには起動時に`git rev-parse --short HEAD`で取得した`website`/`website-contents`のコミットハッシュを含むため、更新後に変更が正しく反映されているか確認できます。
- アクセスログは`logs/access.log`にJSONL形式で記録されます。ログエントリには `id`/`url`/`status`/`method`/`client`/`headers`/`managers`(pp/csp/timings/network)が含まれます。
- 5XXエラーが発生した場合は`logs/error.log`にPythonのトレースバックが記録されます。リクエストIDでアクセスログと照合できます。
- リクエストIDは[FourWord ID](https://github.com/nercone-dev/fourword/)形式が採用されており、テキスト形式に変換された後`X-Request-Id`レスポンスヘッダーとして返されます。`app.log`ファイルではある程度幅が狭いターミナルでも折り返しが発生しないよう、Compact Text形式が使用されています。 
- `Server-Timing`ヘッダーで各処理段階の所要時間を確認できます。
