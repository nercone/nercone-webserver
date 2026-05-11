from http import HTTPStatus
from fastapi import Request, Response
from fastapi.templating import Jinja2Templates

default_messages = {
    400: "リクエストの構文が正しくないか、パラメータが不正です。",
    401: "このリソースにアクセスするには認証が必要です。",
    402: "このリソースへのアクセスには支払いが必要です。",
    403: "このリソースへのアクセス権がありません。",
    404: "リクエストしたページまたはリソースが見つかりません。",
    405: "このリソースではそのHTTPメソッドは許可されていません。",
    406: "リクエストのAcceptヘッダーと一致するレスポンスを生成できません。",
    407: "このリソースにアクセスするにはプロキシの認証が必要です。",
    408: "リクエストが時間内に完了しませんでした。",
    409: "現在のリソースの状態とリクエストが競合しています。",
    410: "リクエストしたリソースは恒久的に削除されました。",
    411: "リクエストにはContent-Lengthヘッダーが必要です。",
    412: "リクエストの前提条件がサーバーの状態と一致しません。",
    413: "リクエストのボディがサーバーの許容サイズを超えています。",
    414: "リクエストURIがサーバーの処理できる長さを超えています。",
    415: "リクエストのメディア形式はサポートされていません。",
    416: "リクエストしたレンジはリソースのサイズ内に存在しません。",
    417: "リクエストのExpectヘッダーの要件をサーバーが満たせません。",
    418: "このサーバーはティーポットです。コーヒーを淹れることはできません。",
    421: "リクエストが意図しないサーバーに到達しました。",
    426: "このリクエストを処理するにはプロトコルのアップグレードが必要です。",
}

default_joke_messages = {
    400: "日本語でおk",
    401: "見たいのならログインすることね",
    402: "夢が欲しけりゃ金払え！",
    403: "あんたなんかに見せるもんですか！",
    404: "そんなページ知らないっ！",
    405: "そのMethodはNot Allowedだよ",
    406: "すまんがその条件ではお渡しできない。",
    407: "うちのプロキシ使うんだったらまずログインしな。",
    408: "もう用がないならさっさと帰りなさい。",
    409: "ちょっと待ったそんな話聞いてないぞ",
    410: "もう無いで。",
    411: "サイズを教えろ。話はそれからだ。",
    412: "なにその条件美味しいの",
    413: "そ、そそ、そんなの入りきらないよっ！",
    414: "もちつけ",
    415: "そんな形式知らない！",
    416: "ちっさぁ:heart:",
    417: "期待させて悪かったわね！",
    418: "ティーポット「私はコーヒーを注ぐためのものではありません！やだっ！」",
    421: "またあいつ案内先間違えてるよ...どうしよ...",
    426: "それに答えるには、まずWebSocketに移動したい。"
}

def error_page(templates: Jinja2Templates, request: Request, status_code: int, message: str | None = None, joke_message: str | None = None) -> Response:
    status_code_name = HTTPStatus(status_code).phrase
    return templates.TemplateResponse(status_code=status_code, request=request, name="error/index.html", context={"status_code": status_code, "status_code_name": status_code_name, "message": message or default_messages.get(status_code, "不明なエラーが発生してしまったようです。ご迷惑をおかけし申し訳ございません..."), "joke_message": joke_message or default_joke_messages.get(status_code, "あんのーん")})
