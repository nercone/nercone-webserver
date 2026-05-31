# CLAUDE.md
このファイルは、Claude Codeがこのリポジトリ内のコードを扱う際に知っておくべき情報を提供するものです。

## 概要
ここは[nercone.dev](https://nercone.dev/)のWebサーバー本体のソースコードを管理しているリポジトリです。

Python 3.12のFastAPI + Uvicornの上で動くASGIアプリケーションです。

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
│   ├── access_counter.txt
│   └── mime.types
├── logs
│   ├── .gitkeep
│   ├── app.log
│   ├── access.log
│   └── error.log
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
- `fastapi`
- `uvicorn[standard]`
- `jinja2`
- `mistune`
- `markitdown`
- `beautifulsoup4`
- `resvg-py`
- `scour`
- `rjsmin`
- `rcssmin`
- `minify-html`
- `httpx[http2]`
- `websockets`
- `fourword`
- `pyyaml`

## 補足
- `/status`エンドポイントのレスポンスには起動時に`git rev-parse --short HEAD`で取得した`website`/`website-contents`のコミットハッシュを含むため、更新後に変更が正しく反映されているか確認できます。
- アクセスログは`logs/access.log`にJSONL形式で記録されます。
- 5XXエラーが発生した場合は`logs/error.log`にPythonのトレースバックが記録されます。
