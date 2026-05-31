# CLAUDE.md
このファイルは、Claude Codeがこのリポジトリ内のコードを扱う際に知っておくべき情報を提供するものです。

## 概要
これは[nercone.dev](https://nercone.dev/)のウェブサーバー本体のソースコードを管理しているリポジトリです。

Python 3.12のFastAPI + Uvicornの上で動くASGIアプリケーションであり、デフォルトでは`0.0.0.0:8080`でリッスンします。環境変数`WEBSITE_UDS`が設定されている場合はUnix Domain Socketを使用します。

本番環境ではNginxがリバースプロキシ兼TLS終端として前段に立ち、Dockerコンテナとして実行されます。

コンテンツ (HTML、Markdown、CSS、画像など) は別リポジトリ`website-contents`で管理されており、`git submodule`を使用し`public/`ディレクトリにマウントされています。

## 関連リポジトリ

| URL | 説明 |
| --- | --- |
| `https://github.com/nercone-dev/website/` | Pythonサーバー本体を管理しています。ルーティング・レンダリング・ミドルウェアなどのサーバーサイド処理のほとんどを担います。 |
| `https://github.com/nercone-dev/website-contents/` | テンプレートやアセットなどのコンテンツを管理しています。`git submodule`を使用し`website`の`public/`ディレクトリにマウントされています。 |

## ディレクトリツリー

### メインリポジトリ
```
https://github.com/nercone-dev/website.git
├── databases
│   ├── .gitkeep
│   ├── access_counter.txt
│   └── mime.types
├── logs
│   ├── .gitkeep
│   ├── app.log
│   ├── access.log
│   └── error.log
├── public -> https://github.com/nercone-dev/website-contents.git
├── src
│   └── nercone_website
│       ├── __init__.py
│       ├── __main__.py
│       ├── constants.py
│       ├── logger.py
│       ├── databases.py
│       ├── manager.py
│       ├── resolver.py
│       ├── templates.py
│       ├── app.py
│       ├── renderer.py
│       └── middleware.py
├── .gitignore
├── .gitmodules
├── README.md
├── CLAUDE.md
├── LICENSE
├── uv.lock
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── update.sh
└── update-contents.sh
```

### コンテンツリポジトリ
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
│   │   │   ├── template
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
│   │   └── ...
│   ├── css
│   │   ├── pages
│   │   │   ├── color-palette.css
│   │   │   ├── daily-quote.css
│   │   │   ├── index.css
│   │   │   ├── links.css
│   │   │   └── qr-code.css
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
│   │   ├── sidebar.js
│   │   └── class-prefix.js
│   └── pgp
│       ├── nenaicone.asc
│       └── nercone.asc
├── about
│   ├── index.md
│   └── server.md
├── error
│   ├── client.md
│   ├── server.html
│   └── nginx.html
├── test
│   ├── html.html
│   ├── markdown.md
│   ├── font-size.md
│   └── sidebar.html
├── base.html
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
├── quotes.txt
├── robots.txt
├── shorturls.json
└── site.webmanifest
```

## 依存関係

| ライブラリ | 用途 |
| --- | --- |
| `fastapi` | ASGIフレームワーク・ルーティング |
| `uvicorn[standard]` | ASGIサーバー |
| `jinja2` | テンプレートエンジン |
| `mistune` | MarkdownをHTMLに変換するパーサー |
| `markitdown` | HTMLをMarkdownに変換するライブラリ |
| `beautifulsoup4` | HTMLのパース |
| `resvg-py` | SVGをPNGにラスタライズする (サムネイル生成用) |
| `scour` | SVGの最小化 |
| `rjsmin` | JavaScriptの最小化 |
| `rcssmin` | CSSの最小化 |
| `minify-html` | HTMLの最小化 (インラインCSS/JSを含む) |
| `httpx[http2]` | HTTP/2対応非同期HTTPクライアント (mime.types取得) |
| `websockets` | WebSocketプロキシ用クライアント |
| `fourword` | リクエストIDの生成 (`scope["id"]`。`.text`と`.compact_text`プロパティを持つ) |
| `pyyaml` | YAMLフロントマターのパース (`pyproject.toml`への明示記載なし・推移的依存) |

## リクエスト処理の流れ

```
クライアント -> Nginx (80/tcp, 443/tcp, 443/quic+udp) -> Uvicorn (8080/tcp or UDS)
    -> Middleware.__call__()
        -> scope に id(FourWord)・pp(PPManager)・csp(CSPManager)・timings(TimingManager)・network(NetworkManager)・options(OptionManager) を設定
        -> ホスト名チェック (network.trusted でない場合、不正なHostヘッダーは403で拒否)
        -> WebSocketの場合はサブドメイン処理のみ行いFastAPIへ直接ディスパッチ
        -> OPTIONS メソッドは204を即時返却
        -> リクエストボディの読み込み (後続処理で再利用できるようにバッファリング)
        -> サブドメイン処理 (例: foo.nercone.dev -> /oof/ にパスを変換して試行し、4XXなら元のパスにフォールバック)
        -> FastAPIルーティング
            -> 専用エンドポイント (/ping, /status, /welcome など)
            -> default_response() -> resolver経由でパスを解決
                -> resolve_page() でHTMLまたはMarkdownファイルを検索
                -> resolve_file() で静的ファイルを検索
                -> resolve_shorturl() で短縮URLを検索
                -> 上記全て失敗 -> 404エラーページ
        -> send() でレスポンスを加工・送信
            -> HTML/CSS/JS/SVGの最小化 (Content-Typeに応じて)
            -> 共通レスポンスヘッダーの付与 (X-Request-Id, Server, Onion-Location, Link, Cache-Control, Referrer-Policy, Permissions-Policy, Content-Security-Policy, CORS)
            -> Server-Timingヘッダーの付与
        -> Logger.log_access() でアクセスログをファイルに書き込み
```

## モジュール詳細

### `constants.py`
サーバー全体で使用する設定・定数を定義する。

- **`unix_socket`** - 環境変数`WEBSITE_UDS`の値。設定されている場合はUnix Domain Socketでリッスンする。
- **`Directories`** - `Path.cwd()`を起点としたディレクトリパス群。サーバーは`website/`をCWDとして起動する必要がある。
- **`Files`** - 各種ファイルへの絶対パス。`Files.Logs`サブクラスに`app`・`access`・`error`の3つのログファイルパスを持つ。
- **`Repositories`** - 起動時に`git`コマンドを実行してリモートURLとコミットハッシュ(short)を取得する。`Server`・`Contents`のサブクラスにそれぞれ`url`・`version`属性を持ち、テンプレートに`Repositories`オブジェクトとして公開される。
- **`Hostnames`** - 受け付けるホスト名のリスト。`www`・`tor`・`local`に分類される。`public = www + tor`、`all = local + public`。

### `app.py`
FastAPIアプリケーション本体。起動時に`MimeTypes.load()`を呼び出してMIMEタイプを登録する。

**主要なエンドポイント:**

| パス | 説明 |
| --- | --- |
| `GET /ping` | ヘルスチェック。`pong!`を返す。 |
| `GET /status` | サーバー・コンテンツのバージョン・日替わり迷言・アクセスカウンターをJSONで返す。 |
| `GET /welcome` | AAアートのウェルカムメッセージをプレーンテキストで返す。 |
| `GET /assets/images/thumbnail/template/{template}` | クエリパラメータ(`path`・`title`・`description`)を受け取りPNG画像を生成する。 |
| `GET /error/{status_code}` | 指定したステータスコード(数値・`"server"`・`"nginx"`)のエラーページを表示する。 |
| `GET,POST,HEAD /{path:path}` | すべての未マッチリクエストを`default_response()`に委譲する。 |

### `templates.py`
Jinja2テンプレートのセットアップとグローバル変数・フィルタの定義を行う。`access_counter`インスタンスもここで生成される。

**Jinja2グローバル変数:**

| 変数名 | 内容 |
| --- | --- |
| `access_counter` | AccessCounterオブジェクト。テンプレートから`access_counter.get()`でカウンター値を参照できる。 |
| `Repositories` | Repositoriesクラス。`Repositories.Server.version`・`Repositories.Contents.version`などを参照できる。 |
| `Hostnames` | Hostnamesクラス。`Hostnames.tor[0]`などを参照できる。 |
| `this_year` | 現在の年 (Asia/Tokyo) を返す関数 |
| `this_year_in_heisei` | 現在の年を平成換算で返す関数 |
| `get_daily_quote` | UTCの日付をシードとして`quotes.txt`からランダムに迷言を返す関数 |

**Jinja2フィルタ:**

| フィルタ名 | 内容 |
| --- | --- |
| `re_sub` | `re.sub(pattern, repl, s)` を呼び出す正規表現置換 |

### `resolver.py`
パス解決ロジックを担う。`renderer.py`・`middleware.py`から利用される。

**パス解決の優先順位:**
1. `resolve_page()` - HTMLテンプレートまたはMarkdownファイルを以下の順で探す:
   - `{path}.html`, `{path}/index.html`, `{path}/README.html`
   - `{path}.md`, `{path}/index.md`, `{path}/README.md`
   - 拡張子`.html`または`.md`で終わるパスは、拡張子を除いた上で同様の候補を検索する
   - Markdownモードの場合は`.md`候補を`.html`候補より先に検索する
2. `resolve_file()` - 静的ファイルとして直接配信する。`public/`ディレクトリ外へのパストラバーサルは`PermissionError`で拒否する。
3. `resolve_shorturl()` - `shorturls.json`の`redirect`エントリは直接リダイレクト先URLを返し、`alias`エントリは別のキーに解決し直す(最大10回の連鎖)。

### `renderer.py`
レンダリング・エラーページ生成・サムネイル生成を担う。

**Markdownモード:**
以下の条件のいずれかを満たすリクエストはMarkdownとして配信される:
- リクエストのパスが`.md`で終わる
- `Accept`ヘッダーに`text/markdown`が含まれる
- `User-Agent`が`curl`・`claude-user`・`chatgpt-user`・`google-extended`・`perplexity-user`のいずれかを含む

HTMLファイルの場合、Jinja2でレンダリング後にBeautifulSoupで`<main>`タグを抽出し、`markitdown`でMarkdownに変換して配信する。

**Markdownレンダリングパイプライン (.mdファイルの通常表示):**
1. YAMLフロントマター(存在する場合)をパースしてJinja2ブロック変数として展開する
2. 本文をJinja2テンプレートとしてレンダリングする (テンプレートのグローバル変数が使用可能)
3. `mistune`でHTMLに変換する (`CustomHTMLRenderer`によりGitHub Alertsのブロック記法をサポート)
4. フロントマターの`base`キーがあればそのテンプレートを、なければ`/base.html`を継承したJinja2テンプレートとして組み立て最終HTMLを生成する

**テンプレートコンテキスト:**
`default_response()`冒頭で`context.update(request.scope)`を行うため、`options`・`csp`・`pp`・`timings`・`network`などのスコープ変数がJinja2テンプレート内から直接参照できる。

**ETagサポート:**
ページ・静的ファイルともにSHA-256ベースのETagを生成し、`If-None-Match`が一致する場合は304を返す。

**エラーページ:**
- 4XX系: `error/client`テンプレート(Markdown)をJinja2でレンダリング。`status_code`・`status_code_name`・`message`・`joke_message`をコンテキストとして渡す。
- 5XX系(502/503/504以外): `error/server`テンプレート(HTML)をレンダリングなしで配信。
- 502/503/504: `error/nginx`テンプレート(HTML)をレンダリングなしで配信。

**サムネイル生成:**
`assets/images/thumbnail/template/{template}.svg`のSVGテンプレート内の`__PATH__`・`__TITLE__`・`__DESCRIPTION__`プレースホルダーを置換した後、`resvg_py`で1280×640pxのPNGにラスタライズする。フォントとして`NerconeSansJP`・`NerconeMonoJP`の各ウェイトを使用する。

### `middleware.py`
Starlette互換のASGIミドルウェアとして実装されている(Starlette標準の`BaseHTTPMiddleware`は使用していない)。

**付与するレスポンスヘッダー:**

| ヘッダー | 内容 |
| --- | --- |
| `X-Request-Id` | FourWordによるリクエストID |
| `Server` | `nercone.dev ({server_version}+{contents_version})` |
| `Onion-Location` | Torオニオンサービスの対応URL |
| `Link` | サイトマップ・robots.txtへのリンク |
| `Cache-Control` | 既存ヘッダーがない場合に`no-cache`を付与 |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | PPManagerの内容 (カメラ・マイクなど全て無効) |
| `Content-Security-Policy` | CSPManagerの内容 |
| `Access-Control-Allow-Origin` | フォント/画像/CSS/JSは`*`、同一ドメインからのリクエストはoriginを設定 |
| `Server-Timing` | TimingManagerの内容 |

**最小化対象:**

| Content-Type | 使用ライブラリ |
| --- | --- |
| `text/html` | `minify_html` |
| `text/css` | `rcssmin` |
| `text/javascript` / `application/javascript` | `rjsmin` |
| `image/svg+xml` | `scour` |

### `manager.py`
スコープに格納される各種マネージャークラスを提供する。

- **`PPManager`** - `Permissions-Policy`ヘッダーを管理する。デフォルトでカメラ・マイク・位置情報など主要な権限を全て無効化。`set()`・`append()`・`remove()`で制御し、`header`プロパティでヘッダー文字列を生成する。
- **`CSPManager`** - `Content-Security-Policy`ヘッダーを管理する。デフォルトで`'self'`と`assets.nercone.dev`を許可。`set()`・`append()`・`remove()`で制御し、`header`プロパティでヘッダー文字列を生成する。エラーページのように外部フォントが必要な場合はfont-src等を動的に追加する。
- **`TimingManager`** - `Server-Timing`ヘッダーを管理する。`start(key)`・`stop(key)`でタイミング計測し、`header`プロパティで文字列を生成する。
- **`NetworkManager`** - クライアントIPの信頼判定を行う。RFC 1918プライベート・ループバック・APIPA・CGNATなどを信頼済みとする。Unix Domain Socket使用時は`address=None`が渡され`trusted=False`になる(代わりにNginxの`X-Real-IP`ヘッダーを`host`として使用する)。
- **`OptionManager`** - クエリパラメータとCookieを統合してオプションを取得するヘルパークラス。クエリパラメータのほうがCookieより優先される。`{key}.once`クエリパラメータはCookieに保存されない一時的な値として扱われる。クエリパラメータに値がある場合はCookieにも同期する(`apply()`メソッド)。

### `logger.py`
ファイルベースのロガー。全メソッドはstatic。

- **`Logger.log(*contents, path)`** - 任意のテキストを指定ファイルに追記する。デフォルト出力先は`logs/app.log`。`fcntl.flock`で排他制御。
- **`Logger.log_access(request, response)`** - アクセスログをJSONとして`logs/access.log`に記録し、サマリ行を`logs/app.log`にも記録する。リクエスト・レスポンスヘッダー・各マネージャーの状態が含まれる。
- **`Logger.log_error(id, traceback)`** - トレースバックを`logs/error.log`に記録し、エラーサマリを`logs/app.log`にも記録する。

### `databases.py`
**`MimeTypes`クラス:** Apache HTTPDのmime.typesをリモートから取得しファイルキャッシュ(30日)する。起動時に`__main__.py`が`fetch()`を呼び出し、`app.py`が`load()`を呼び出してPythonの`mimetypes`モジュールに追加登録する。

**`AccessCounter`クラス:** ファイルベース(`databases/access_counter.txt`)のアクセスカウンター。`fcntl.flock`による排他ロックでインクリメントする。`get()`で現在値を返し、`increase()`でインクリメントする。カウンターはページレンダリング成功時に呼ばれる。

## 開発・デバッグのヒント
- `/status`エンドポイントはサーバー・コンテンツのコミットハッシュとアクセスカウンターを返すため、デプロイ後の確認に便利です。
- アクセスログは`logs/access.log`に1行1JSONエントリで記録されます。`jq`コマンドで解析できます。
- 5XXエラーが発生した場合は`logs/error.log`にPythonのトレースバックが記録されます。
- Unix Domain Socketを使用する場合は環境変数`WEBSITE_UDS`にソケットパスを設定します。
