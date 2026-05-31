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
- アクセスログは`logs/access.log`にJSONL形式で記録されます。
- 5XXエラーが発生した場合は`logs/error.log`にPythonのトレースバックが記録されます。
