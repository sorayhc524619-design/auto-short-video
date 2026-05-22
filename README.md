# BGM YouTube Channel - Automation Pipeline

アメリカ向け **Cinematic Sleep Music** チャンネルを副業として運営するための自動生成パイプライン。
Claude / Suno / Stability AI / ffmpeg / YouTube Data API を組み合わせ、
テーマ生成 → 音楽生成 → 映像生成 → 合成 → 自動アップロードを一気通貫で行います。

## なぜ Sleep Music なのか

- 1再生あたりの視聴時間が圧倒的に長い（夜つけっぱなし）
- 米国の不眠人口が多くニーズ巨大
- 平均RPM **$4.38**（音楽動画ジャンル）
- 1動画 3〜8時間で運用すれば、登録者が同じでも収益額は他ジャンルの数倍

**ただし重要**: 2025年7月施行のYouTube「Inauthentic Content」ポリシーでAI生成オンリーは40%以上が収益化拒否。本パイプラインは下記で対策しています：

- 動画ごとに具体的なシネマティック世界観をClaudeに生成させる（"Rainy Tokyo Apartment" 等）
- Stability AIで動画ごとに違うビジュアルを複数枚
- Ken Burns ループでビジュアルに動きを与える
- 環境音をミックスして音響に独自性を出す
- カスタムサムネ・英語SEO最適化メタデータ

## アーキテクチャ

```
Agent 1: agent1_theme.py    Claude → theme JSON (英語タイトル, Sunoプロンプト×5, ビジュアルプロンプト)
Agent 2: agent2_music.py    Suno API → mp3 ×5 トラック
Agent 3: agent3_visual.py   Stability AI → 1920x1080画像 ×3 → Ken Burns mp4
Agent 4: agent4_compose.py  ffmpeg → クロスフェード結合 + 環境音MIX + 映像ループ + タイトルカード
Agent 5: agent5_upload.py   YouTube Data API → 動画 + サムネアップロード
```

## セットアップ手順（ゼロから）

### 1. YouTubeチャンネル作成
- Googleアカウントで新規YouTubeチャンネルを作成
- ブランドアイコン・バナーを設定（Canvaで作成推奨）
- チャンネル名: 例 "Cozy Dreams BGM" / "Whisper Sleep Lab" など、ジャンル＋世界観を入れる

### 2. Google Cloud で YouTube Data API v3 を有効化
- https://console.cloud.google.com/ → 新規プロジェクト
- "YouTube Data API v3" を有効化
- 「OAuth 同意画面」を作成（外部, テストユーザーに自分のメールを追加）
- 「認証情報」→ OAuth 2.0 クライアントID → デスクトップアプリ で作成
- client_id / client_secret を控える

### 3. API キーを揃える
| API | 取得元 | 費用目安 |
|---|---|---|
| Claude | https://console.anthropic.com | 1動画 $0.05〜 |
| Suno | https://sunoapi.org など | Suno Pro $10/月 + API従量 |
| Stability AI | https://platform.stability.ai | 1画像 $0.01〜 |
| YouTube | Google Cloud (無料) | 無料 |

### 4. 環境変数設定
```bash
cp .env.example .env
# .env を編集して全APIキーを設定
```

### 5. YouTube OAuth トークン取得
```bash
python setup_youtube_auth.py --client-id YOUR_CLIENT_ID --client-secret YOUR_SECRET
# ブラウザが開いてGoogle認証 → .env に YOUTUBE_CREDENTIALS_JSON が自動追加される
```

### 6. 環境音アセットを配置
`ambient/README.md` 参照。`rain.mp3` `fireplace.mp3` 等を Freesound 等から DL して配置。

### 7. ffmpeg をインストール
```bash
# Linux
sudo apt-get install ffmpeg fonts-dejavu-core
# Mac
brew install ffmpeg
```

### 8. Python 依存
```bash
pip install -r requirements.txt
```

## 実行

```bash
# 10分尺でテスト（投稿はしない）
python main.py --dry-run --duration 600

# 3時間版でテスト投稿（unlisted 推奨）
# .env で YOUTUBE_PRIVACY_STATUS=unlisted にしてから
python main.py --duration 10800

# 本番（3h、公開）
python main.py
```

## GitHub Actions で毎日自動投稿

`.github/workflows/daily_video.yml` が既に用意されています。

1. リポジトリの Settings → Secrets に以下を登録:
   - `CLAUDE_API_KEY`
   - `SUNO_API_KEY`
   - `SUNO_API_BASE_URL`（任意）
   - `STABILITY_API_KEY`
   - `YOUTUBE_CREDENTIALS_JSON`
2. デフォルトで UTC 02:00 (JST 11:00) に毎日実行
3. 8時間動画を生成する場合は workflow_dispatch から手動実行推奨（GH Actionsの無料枠を超える可能性あり、self-hosted runner 検討）

## 副業として成立させるロードマップ

| フェーズ | 期間 | やること | 目標 |
|---|---|---|---|
| 0. 準備 | 1週間 | チャンネル作成 / API揃え / テスト投稿 | dry-run動画1本完成 |
| 1. 初動 | 1〜3ヶ月 | 週3〜5本、テーマ毎にバリエーション | 登録100、視聴4000h |
| 2. 収益化 | 3〜6ヶ月 | YPP申請 → 通過 → 8h動画開始 | YPP通過 |
| 3. スケール | 6ヶ月〜 | 投稿頻度↑、テーマ別シリーズ化 | $300/月〜 |

### 収益化のための重要ポイント
1. **チャンネル開設後すぐ収益化申請しない** — 30本以上、独自のテーマ性が見える状態にしてから申請する方が通りやすい
2. **動画ごとにテーマを変える** — 同じ画像/同じBGMの使い回しは即NG
3. **タイトル・サムネ・説明を毎回手で微調整する習慣** — 完全自動投稿だとアルゴリズムに見抜かれやすい。`--dry-run` で確認 → 微修正 → アップロードの運用がおすすめ
4. **3ヶ月は耐える** — 最初の50本くらいは伸びない。データを溜める期間

## ライセンス・規約上の注意

- Suno で生成した曲を商用利用するには **Suno Pro ($10/月) 以上** の契約が必要
- Stability AI の出力は商用OK（要規約確認）
- Freesound から環境音を使う場合は CC ライセンスを確認し、必要なら動画説明欄にクレジット表記
- YouTube の Inauthentic Content ポリシーを定期的にチェック
