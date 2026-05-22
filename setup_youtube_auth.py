"""
setup_youtube_auth.py - YouTube OAuth2認証セットアップ
このスクリプトを一度だけ実行して、YouTubeの投稿権限トークンを取得します。

実行方法:
  python setup_youtube_auth.py --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
"""

import argparse
import json
import os
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import urllib.parse


AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube"
REDIRECT_URI = "http://localhost:8080"

auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        params = parse_qs(urlparse(self.path).query)
        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h1>Success! Please close this tab.</h1>".encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # ログ抑制


def get_tokens(client_id, client_secret, code):
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()

    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-id", required=True, help="GoogleクライアントID")
    parser.add_argument("--client-secret", required=True, help="Googleクライアントシークレット")
    args = parser.parse_args()

    # 認証URLを生成
    params = urllib.parse.urlencode({
        "client_id": args.client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    })
    url = f"{AUTH_URL}?{params}"

    print("=" * 60)
    print("YouTube認証セットアップ")
    print("=" * 60)
    print("\nブラウザが開きます。Googleアカウントでログインして許可してください。")
    print("（ブラウザが開かない場合は以下のURLをコピーして開いてください）")
    print(f"\n{url}\n")

    webbrowser.open(url)

    # ローカルサーバーで認証コードを受け取る
    print("認証待機中...")
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server.handle_request()

    if not auth_code:
        print("❌ 認証コードの取得に失敗しました")
        return

    print("✅ 認証コード取得成功。トークンを取得中...")

    # トークン取得
    tokens = get_tokens(args.client_id, args.client_secret, auth_code)

    # .envに書き込む形式でJSONを生成
    credentials = {
        "token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token"),
        "client_id": args.client_id,
        "client_secret": args.client_secret,
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": SCOPE.split(),
    }

    credentials_json = json.dumps(credentials)

    # .envファイルを更新
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()

        if "YOUTUBE_CREDENTIALS_JSON=" in content:
            lines = content.splitlines()
            new_lines = []
            for line in lines:
                if line.startswith("YOUTUBE_CREDENTIALS_JSON="):
                    new_lines.append(f"YOUTUBE_CREDENTIALS_JSON={credentials_json}")
                else:
                    new_lines.append(line)
            content = "\n".join(new_lines)
        else:
            content += f"\nYOUTUBE_CREDENTIALS_JSON={credentials_json}"

        with open(env_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ .envファイルに認証情報を保存しました: {env_path}")
    else:
        print("⚠️ .envファイルが見つかりません。以下をコピーして .env に追加してください:")
        print(f"\nYOUTUBE_CREDENTIALS_JSON={credentials_json}")

    print("\n🎉 YouTube認証セットアップ完了！")
    print("これでpython main.pyで実際にYouTubeに投稿できます。")


if __name__ == "__main__":
    main()
