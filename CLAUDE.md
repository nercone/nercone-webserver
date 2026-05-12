# CLAUDE.md
このファイルは、Claude Codeがこのリポジトリ内のコードを扱う際に知っておくべき情報を提供するものです。

## 概要
これは[nercone.dev](https://nercone.dev/)のウェブサーバー本体のソースコードを管理しているリポジトリです。

Python 3.12のFastAPI + Uvicornの上で動くASGIアプリケーションであり、`0.0.0.0:8080`でリッスンします。

本番環境ではNginxがリバースプロキシ兼TLS終端として前段に立ち、GCP Compute Engine (AlmaLinux 10)上のsystemdサービス(`nercone-website.service`)として常駐しています。

コンテンツ (HTML、Markdown、CSS、画像など) は別リポジトリ`website-contents`で管理されており、`git submodule`を使用し`public/`ディレクトリにマウントされています。

## 関連リポジトリ

| URL                                                | 説明                                                                                                                   |
| -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `https://github.com/nercone-dev/website/`          | Pythonサーバー本体を管理しています。ルーティング・レンダリング・ミドルウェアなどのサーバーサイド処理のほとんどを担います。                |
| `https://github.com/nercone-dev/website-contents/` | テンプレートやアセットなどのコンテンツを管理しています。`git submodule`を使用し`website`の`public/`ディレクトリにマウントされています。 |

## ディレクトリツリー

### メインリポジトリ
```
https://github.com/nercone-dev/website.git
├── databases
│   ├── .gitkeep
│   └── access_counter.db - database.pyによって生成・管理される、アクセスカウンターの数値を記録するためのsqlite3データベース
├── logs
│   ├── .gitkeep
│   ├── access.log - logger.pyによって生成されるJSONL形式のアクセスログ
│   └── uvicorn.log - uvicornによって生成される1行ずつのシンプルなログ (Pythonトレースバックを含む)
├── public -> https://github.com/nercone-dev/website-contents.git
├── src
│   └── nercone_website
│       ├── __init__.py
│       ├── __main__.py - コマンドとして実行した際のエントリーポイント。Uvicornの起動設定を行う。
│       ├── config.py - パス定義・ホスト名・エラーメッセージ・レスポンスヘッダー・IP信頼判定などの共通設定
│       ├── logger.py - access.logを生成するためのJSONLロガー
│       ├── database.py - アクセスカウンターのSQLiteデータベースを管理するモジュール
│       ├── server.py - Jinja2テンプレートのグローバル変数定義・FastAPIルート定義を行うメインモジュール
│       ├── proxy.py - HTTPおよびWebSocketのリバースプロキシ機能を提供するユーティリティ
│       ├── renderer.py - ページのパス解決・HTML/Markdownレンダリング・短縮URL解決・サムネイル生成を行うモジュール
│       └── middleware.py - ヘッダー管理・CSS/JS/SVG最小化・ホスト名チェック・サブドメインルーティングを行うミドルウェア
├── README.md
├── CLAUDE.md
├── LICENSE - MITライセンス
├── pyproject.toml - Pythonプロジェクト設定用ファイル
├── start.sh - 本番環境向けのサーバー起動用スクリプト
├── update.sh - 本番環境向けのサーバー自動更新用スクリプト
├── update-contents.sh - サーバー自体には変更がなく、サブモジュールにのみ変更がある場合のための手動更新用スクリプト
├── nercone-website.service - メインのsystemdサービス (実行内容はsudo bash start.shと同等)
├── nercone-website-autoupdater.service - 自動更新用のsystemdサービス (実行内容はsudo bash update.shと同等)
└── nercone-website-autoupdater.timer - 自動更新用のsystemdタイマー (毎日0:00 UTCに起動)
```

`config.py`の`Directories.public`は`Path.cwd() / "public"`で解決されます。そのため、サーバーは必ず`website/`ディレクトリをカレントディレクトリとして起動しなければなりません。

`update.sh`/`update-contents.sh`は(ネストされたサブモジュールを含む)全てのサブモジュールを再帰的に取得・マージするため、publicのコミットIDの変更をリモートに反映する必要はありません。

UvicornのログにはPythonのトレースバックを含むため、5XXエラーなどの際のデバッグのために`uvicorn.log`を生成するように設定しています。

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
│   ├── images - 画像
│   │   ├── dotcat
│   │   │   ├── 2nd
│   │   │   │   └── ...
│   │   │   ├── forks
│   │   │   │   └── ...
│   │   │   ├── labs
│   │   │   │   └── ...
│   │   │   ├── os
│   │   │   │   └── ...
│   │   │   ├── step
│   │   │   │   └── ...
│   │   │   ├── icon.ai
│   │   │   ├── icon.png
│   │   │   ├── icon.svg
│   │   │   ├── icon.webp
│   │   │   ├── icon-rounded.ai
│   │   │   ├── icon-rounded.png
│   │   │   ├── icon-rounded.svg
│   │   │   ├── icon-rounded.webp
│   │   │   ├── icon-mask.ai
│   │   │   ├── icon-mask.png
│   │   │   ├── icon-mask.svg
│   │   │   ├── icon-mask.webp
│   │   │   ├── icon-mask-inverted.ai
│   │   │   ├── icon-mask-inverted.png
│   │   │   ├── icon-mask-inverted.svg
│   │   │   ├── icon-mask-inverted.webp
│   │   │   ├── banner.ai
│   │   │   ├── banner.png
│   │   │   ├── banner.svg
│   │   │   └── banner.webp
│   │   ├── thumbnails
│   │   │   ├── error.svg - エラーページ用サムネイルテンプレート
│   │   │   └── normal.svg - 通常ページ用サムネイルテンプレート
│   │   └── ...
│   ├── fonts - フォント
│   │   ├── InterBIZUD-Bold.ttf
│   │   ├── InterBIZUD-BoldItalic.ttf
│   │   ├── InterBIZUD-Italic.ttf
│   │   ├── InterBIZUD-Regular.ttf
│   │   ├── MesloBIZUD-Bold.ttf
│   │   ├── MesloBIZUD-BoldItalic.ttf
│   │   ├── MesloBIZUD-Italic.ttf
│   │   ├── MesloBIZUD-Regular.ttf
│   │   ├── MesloLGSNerdFont-Bold.woff2
│   │   ├── MesloLGSNerdFont-BoldItalic.woff2
│   │   ├── MesloLGSNerdFont-Italic.woff2
│   │   └── MesloLGSNerdFont-Regular.woff2
│   ├── css
│   │   ├── pages - ページ固有のスタイル
│   │   │   ├── big-text.css
│   │   │   ├── color-palette.css
│   │   │   ├── index.css
│   │   │   ├── links.css
│   │   │   └── qr-code.css
│   │   ├── themes - テーマ切り替え機能 (未完成)
│   │   │   ├── dark.css
│   │   │   └── light.css
│   │   ├── main.css - メイン/共通
│   │   ├── fonts.css - フォント
│   │   ├── colors.css - カラーパレット
│   │   ├── cursor.css - カスタムカーソル
│   │   ├── view-transition.css - ページ遷移時アニメーション
│   │   ├── loading-overlay.css - アクセス時のオーバーレイアニメーション
│   │   └── sidebar.css - サイドバーレイアウト
│   ├── js
│   │   ├── pages - ページ固有のスクリプト
│   │   │   └── index.js
│   │   ├── main.js - メイン/共通
│   │   ├── cursor.js - カスタムカーソル
│   │   ├── view-transition.js - ページ遷移時アニメーション
│   │   ├── loading-overlay.js - アクセス時のオーバーレイアニメーション
│   │   ├── sidebar.js - サイドバーレイアウト採用のページでのスクロール時のサイドバー上のリンクのアクティブ状態の動的変更
│   │   └── class-prefix.js - small: などのclass属性内のプレフィックスの処理機能
│   └── pgp - PGP公開鍵
│       ├── nenaicone.asc
│       └── nercone.asc
├── about
│   ├── index.md - 自己紹介ページ
│   └── server.md - サーバー情報ページ
├── error
│   ├── index.html - エラーページのテンプレート
│   └── nginx.html - Nginxがプロキシ失敗時に表示するHTMLファイル
├── test
│   ├── html.html - HTML処理のテスト
│   ├── markdown.md - Markdown処理のテスト
│   ├── font-family.md - フォントファミリーのテスト
│   ├── font-size.md - フォントサイズのテスト
│   └── sidebar.html - サイドバーのテスト
├── base.html - 全ページのベーステンプレート
├── index.html - トップページ
├── links.html - 相互リンク一覧
├── download-banner.md - バナーのダウンロードページ
├── projects.html - プロジェクト一覧
├── public-key.html - PGP公開鍵のダウンロードページ
├── color-palette.md - カラーパレットの紹介ページ
├── daily-quote.html - 日替わり迷言集ページ
├── access-counter.html - アクセスカウンター
├── qr-code.html - トップページのQRコード
├── vulnerability-reporters.html - security.txtのAcknowledgmentsに設定してあるページ
├── sitemap.xml - クローラー向けサイトマップ
├── quotes.txt - 日替わり迷言集 (1行1エントリ、UTCの日付をシードとしてランダム選択)
├── robots.txt - RFC 9309
├── shorturls.json - 短縮URL設定
└── site.webmanifest - PWA
```

## 主要な依存ライブラリ

| ライブラリ            | 用途                                                                     |
| ------------------- | ----------------------------------------------------------------------- |
| `fastapi`           | ASGIフレームワーク・ルーティング                                             |
| `uvicorn[standard]` | ASGIサーバー                                                              |
| `jinja2`            | HTMLテンプレートエンジン (テンプレート内でPython式を使用可能)                    |
| `mistune`           | MarkdownをHTMLに変換するパーサー                                            |
| `markitdown`        | HTMLをMarkdownに変換するライブラリ (Markdown配信モード用)                     |
| `beautifulsoup4`    | HTMLのパース (`<main>`タグの抽出など)                                       |
| `resvg-py`          | SVGをPNGにラスタライズする (サムネイル生成用)                                  |
| `scour`             | SVGの最小化                                                               |
| `rjsmin`            | JavaScriptの最小化                                                        |
| `rcssmin`           | CSSの最小化                                                               |
| `httpx[http2]`      | アップストリームへのHTTP/2対応非同期HTTPクライアント (プロキシ・Google Fonts取得) |
| `websockets`        | WebSocketプロキシ用クライアント                                             |

## リクエスト処理の流れ

```
クライアント -> [Nginx (TLS終端・リバースプロキシ)] -> Uvicorn:8080
    -> Middleware.__call__()
        -> ホスト名チェック (不正なHostヘッダーは400で拒否)
        -> サブドメイン処理 (例: foo.nercone.dev -> /oof/ にパスを変換して試行)
        -> AccessSources.is_trusted() でIP信頼判定 -> scope["trusted"] に格納
        -> FastAPIルーティング
            -> 専用エンドポイント (/ping, /status, /welcome など)
            -> default_response() -> renderer.render()
                -> resolve_page() でHTMLまたはMarkdownファイルを検索
                -> resolve_file() で静的ファイルを検索
                -> resolve_shorturl() で短縮URLを検索
                -> 上記全て失敗 -> 404エラーページ
        -> _send() でレスポンスを加工・送信
            -> CSS/JS/SVGの最小化 (Content-Typeに応じて)
            -> 共通レスポンスヘッダーの付与
            -> Server-Timingヘッダーの付与
    -> logger.finalize_log() でJSONLアクセスログを書き込み
```

## モジュール詳細

### `config.py`
サーバー全体で使用する設定・定数を定義する。

- **`Directories`** - `Path.cwd()`を起点としたディレクトリパス群。サーバーは`website/`をCWDとして起動する必要がある。
- **`Files`** - 各種ファイルへの絶対パス。
- **`Repositories`** - 起動時に`git`コマンドを実行してリモートURLとコミットハッシュ(short)を取得する。`Server.version`と`Contents.version`としてテンプレートに公開される。
- **`ErrorMessages`** - HTTPステータスコード別のエラーメッセージ。`normal`(真面目版)と`joke`(ネタ版)の2種類を持つ。エラーページ(`error/index.html`)はJinja2テンプレートとしてレンダリングされ、両方のメッセージが渡される。
- **`Hostnames`** - 受け付けるホスト名のリスト。`local`・`normal`・`onion`に分類される。信頼されていないIPからの不正なHostヘッダーによるアクセスは400で拒否される。
- **`AccessSources`** - 信頼されたIPアドレス範囲 (RFC 1918プライベート・ループバック・APIPA・CGNATなど)。`X-Forwarded-For`ヘッダーを考慮したうえで実質的な送信元IPが信頼範囲内かどうかを判定する。`scope["trusted"]`としてミドルウェアが設定する。
- **`Options`** - Content-Security-Policy・その他のレスポンスヘッダー・Scourの最小化オプションを定義する。
- **`UserOptions`** - クエリパラメータとCookieを統合してオプションを取得するヘルパークラス。クエリパラメータのほうがCookieより優先される。クエリパラメータに値がある場合はCookieにも同期する。

### `server.py`
FastAPIアプリケーション本体。Jinja2のグローバル変数とルートを定義する。

**Jinja2グローバル変数:**

| 変数名                   | 内容                                                    |
| ----------------------- | ------------------------------------------------------- |
| `get_access_count`      | 現在のアクセスカウンター値を返す関数                          |
| `server_version`        | サーバーリポジトリの短いコミットハッシュ                       |
| `contents_version`      | コンテンツリポジトリの短いコミットハッシュ                     |
| `onion_site_url`        | Torオニオンサービスの完全URL                                |
| `this_year`             | 現在の年 (Asia/Tokyo) を返す関数                           |
| `this_year_in_heisei`   | 現在の年を平成換算で返す関数                                 |
| `get_daily_quote`       | UTCの日付をシードとして`quotes.txt`からランダムに迷言を返す関数 |

**Jinja2フィルタ:**

| フィルタ名 | 内容                                             |
| ---------- | --------------------------------------------- |
| `re_sub`   | `re.sub(pattern, repl, s)` を呼び出す正規表現置換 |

**主要なエンドポイント:**

| パス                                    | 説明                                                                               |
| --------------------------------------- | --------------------------------------------------------------------------------- |
| `GET /ping`                             | ヘルスチェック。`pong!`を返す。                                                       |
| `GET /status`                           | サーバー・コンテンツのバージョン・日替わり迷言・アクセスカウンターをJSONで返す。               |
| `GET /welcome`                          | AAアートのウェルカムメッセージをプレーンテキストで返す。                                   |
| `GET /assets/css/google-fonts.css`      | Google FontsのCSSをプロキシし、24時間インメモリキャッシュする。                           |
| `GET /assets/images/thumbnails/generate`| クエリパラメータ(`path`・`title`・`description`・`template`)を受け取りPNG画像を生成する。 |
| `GET /error/nginx`                      | Nginxのエラーページ(`error/nginx.html`)を模擬表示する。                                |
| `GET /error/{status_code}`              | 指定したステータスコードのエラーページを表示する。                                         |
| `GET,POST,HEAD /{full_path:path}`       | すべての未マッチリクエストを`renderer.render()`に委譲する。                              |

`/echo`エンドポイントはルート定義上は`app.api_route`で登録されておらず、独立した関数として実装されているが、`scope["trusted"]`が`True`の場合のみアクセスログのJSON内容をそのまま返すデバッグ用エンドポイントである。

### `renderer.py`
ページのパス解決・レンダリング・短縮URL解決・サムネイル生成を担う。

**パス解決の優先順位:**
1. `resolve_page()` - HTMLテンプレートまたはMarkdownファイルを以下の順で探す:
   - `{path}.html`, `{path}/index.html`, `{path}/README.html`
   - `{path}.md`, `{path}/index.md`, `{path}/README.md`
   - 拡張子`.html`または`.md`で終わるパスは、拡張子を除いた上で同様の候補を検索する
2. `resolve_file()` - 静的ファイルとして直接配信する。`public/`ディレクトリ外へのパストラバーサルは`PermissionError`で拒否する。
3. `resolve_shorturl()` - `shorturls.json`の`redirect`エントリは直接リダイレクト先URLを返し、`alias`エントリは別のキーに解決し直す(最大10回の連鎖)。

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
4. `base.html`を継承したJinja2テンプレートとして組み立て最終HTMLを生成する

**サムネイル生成:**
`assets/images/thumbnails/{template}.svg`のSVGテンプレート内の`__PATH__`・`__TITLE__`・`__DESCRIPTION__`プレースホルダーを置換した後、`resvg_py`で1200×630pxのPNGにラスタライズする。フォントとして`MesloBIZUD-Regular.ttf`・`InterBIZUD-Regular.ttf`・`InterBIZUD-Bold.ttf`を使用する。

### `middleware.py`
Starlette互換のASGIミドルウェアとして実装されている(Starlette標準の`BaseHTTPMiddleware`は使用していない)。

**処理フロー:**
1. ホスト名の検証 - 信頼されていないIPからの不正なHostヘッダーは400で拒否する
2. サブドメインの処理 - サブドメインがある場合は逆順にしてパスのプレフィックスに変換する (例: `foo.bar.nercone.dev/baz` → まず`/rab/oof/baz`を試行し、4XXなら元のパス`/baz`にフォールバックする)
3. リクエストボディの読み込み (後続処理で再利用できるようにバッファリングする)
4. FastAPIアプリへのディスパッチと`_get_response()`によるレスポンス収集
5. `_send()`によるレスポンス加工 (最小化・ヘッダー付与・Server-Timing付与)

末尾スラッシュの正規化として、404になったパスが`/`で終わる場合はスラッシュを除いて再試行する。

**最小化対象:**

| Content-Type              | 使用ライブラリ   |
| ------------------------- | -------------- |
| `text/css`                | `rcssmin`      |
| `text/javascript`         | `rjsmin`       |
| `application/javascript`  | `rjsmin`       |
| `image/svg+xml`           | `scour`        |

HTMLテキスト以外のすべてのレスポンスには`Cache-Control: public, max-age=3600`ヘッダーが付与される(既存のヘッダーがある場合は上書きしない)。

### `logger.py`
アクセスログをJSONL形式で`logs/access.log`に書き込む。

`log_access()`はリクエスト開始時に呼ばれ、ID・タイムスタンプ・送信元IP・ポート・信頼フラグ・スキーム・ホスト・メソッド・パス・リクエストヘッダーを記録する。

`finalize_log()`はレスポンス送信後に呼ばれ、ステータスコード・所要時間(ms)・フェーズ別タイミング(`recv`・`app`・`minify`・`total`など)を追記してファイルに書き込む。

### `database.py`
SQLiteを使用したシンプルなアクセスカウンター。`WAL`モードで動作し、`rowid=1`の単一レコードを`UPDATE`でインクリメントする。アプリ起動時にテーブルとレコードを自動作成する。カウンターはページレンダリング成功時(`render()`内でアクセスカウンターが`None`でない場合)にインクリメントされる。

### `proxy.py`
再利用可能なリバースプロキシファクトリを提供するユーティリティモジュール。`server.py`のルートから呼び出して使用する。

- **`make_http_proxy(base_url_http, headers, remove_prefix_path)`** - HTTPリバースプロキシルートを生成するファクトリ関数。アップストリームの`Server-Timing`ヘッダーは`upstream-`プレフィックスを付けて引き継ぐ。
- **`make_websocket_proxy(base_url_websocket, remove_prefix_path)`** - WebSocketリバースプロキシルートを生成するファクトリ関数。クライアント・サーバー間を双方向に中継する。

## 開発・デバッグのヒント
- ローカル起動時は`website/`ディレクトリで`nercone-website`コマンドを実行する。`public/`サブモジュールが存在しない場合は多くの機能が動作しない。
- `/status`エンドポイントはサーバー・コンテンツのコミットハッシュとアクセスカウンターを返すため、デプロイ後の確認に便利です。
- `/echo`エンドポイントはスコープに格納されたアクセスログJSONをそのまま返すため、ミドルウェアが取得しているリクエスト情報の確認に使用できます。ただしローカルホストなど信頼されたIP範囲からのみ利用可能な点に注意して下さい。
- アクセスログ(`logs/access.log`)の各行はJSON1行であり、`jq`などで解析できます。
- 5XXエラーが発生した場合は`logs/uvicorn.log`にPythonのトレースバックが記録されます。
