# 🎵 Suno AI × YouTube BGMチャンネル 完全ガイド（アメリカ向け）

Sunoで作ったBGMを、アメリカの視聴者向けの長尺動画（1〜3時間）としてYouTubeに自動投稿し、広告収益を狙うためのガイドです。**初心者でも順番にやれば完成する**ように書いています。

---

## 1. なぜ「長尺BGM」なのか（2026年6月時点の調査結果）

ショート動画よりも、**寝る時・勉強する時に流しっぱなしにされる長尺BGM**の方が再生時間（watch hours）が貯まりやすく、収益化に向いています。

| ニッチ | 状況 |
|---|---|
| 睡眠×雨音 (Sleep Soundscapes) | RPM **$10〜25** と高単価、競合約2万チャンネルと少なく成長率14倍の最有力ニッチ |
| ダークアカデミア/ファンタジー | 視聴者の保存率が非常に高く競合が極端に少ない。読書・TRPG勢に刺さる |
| Lofi | 需要は最大だが競合最多（Lofi Girlが1,400万人）。独自ビジュアル必須 |
| 宇宙アンビエント | 睡眠系と相性がよく連続再生時間が長い |

**おすすめは `rain_sleep`（雨音×ピアノ睡眠）から始めること**です。高RPM・低競合・毎晩リピート視聴される性質があるためです。

### ⚠️ 先に知っておくべきルール（重要）

1. **Sunoは有料プラン必須**: 無料プランで作った曲は商用利用（収益化）できません。**Pro（$10/月）以上**に加入してから曲を作ってください。加入中に作った曲は解約後も商用利用OKです。
2. **「静止画1枚＋曲を垂れ流し」はNG**: YouTubeは2026年現在、編集のない静止画AI音楽動画を「再利用コンテンツ/繰り返しの多いコンテンツ」として収益化を却下します。→ このパイプラインは**ゆっくりズームする動きのある映像＋チャプター付きトラックリスト＋独自サムネイル**を自動生成して対策しています。
3. **AI利用の開示**: アップロード時にYouTube Studioの「変更または合成されたコンテンツ」の開示設定をオンにしてください（音楽のみのAI利用は必須ではありませんが、開示しておくのが安全です）。
4. **収益化ライン**: 登録者1,000人＋総再生4,000時間（または登録者500人＋3,000時間で早期アクセス）。長尺BGMは再生時間が貯まりやすいのが強みです。

---

## 2. 全体の流れ

```
Suno（手動・週1回30分）          このリポジトリ（全自動）
┌────────────────┐   ┌──────────────────────────────┐
│ プロンプトをコピペ │ → │ 1時間ミックス生成（フェード+音量正規化）│
│ 8〜10曲生成       │   │ 背景画像+ズーム映像を自動生成          │
│ MP3をダウンロード │   │ 英語タイトル/説明/タグをClaudeが生成   │
│ bgm_input/に置く  │   │ サムネ生成 → YouTubeへ自動投稿        │
└────────────────┘   └──────────────────────────────┘
```

Sunoには公式APIがないため曲作りだけは手動ですが、**それ以外は全部自動**です。

---

## 3. Sunoで曲を作る（手順＋プロンプト）

1. [suno.com](https://suno.com) で **Proプラン（$10/月）** に加入
2. 「Create」→ **Custom**モードをON → **Instrumental**をON
3. 下のプロンプトを**Style of Music欄にコピペ**して生成（1回で2曲できます）
4. 良い曲だけ残して **MP3をダウンロード** → このリポジトリの `bgm_input/` に入れる
5. 1動画あたり**8〜10曲**あれば十分（足りない分は自動ループ）

### 📋 コピペ用Sunoプロンプト

**雨音×睡眠ピアノ（おすすめ・rain_sleep）**
```
ambient sleep music, soft felt piano, gentle rain on window, warm analog pads, 55 bpm, no drums, deeply calming, instrumental
```
```
peaceful sleep ambient, slow piano melody, distant thunder, soft rain texture, lush reverb, dreamy, instrumental, no vocals
```
```
calm nocturne piano, light rainfall ambience, subtle string swells, very slow tempo, soothing bedtime music, instrumental
```

**ダークアカデミア（dark_academia）**
```
dark academia ambience, melancholic solo cello, old library atmosphere, soft vinyl crackle, fireplace warmth, slow classical, instrumental
```
```
fantasy library music, gentle harp and strings, candlelight mood, medieval undertones, mysterious and cozy, instrumental, no vocals
```

**Lofi（lofi_study）**
```
chill lofi hip hop, dusty drums, warm Rhodes piano, vinyl crackle, mellow jazzy chords, 75 bpm, relaxed study beat, instrumental
```

**宇宙アンビエント（space_ambient）**
```
deep space ambient, vast slow pads, cosmic drone, shimmering textures, weightless and serene, no drums, no melody, instrumental
```

全プロンプト一覧は次のコマンドで確認できます:
```bash
python bgm_pipeline.py --list-niches
```

💡 **コツ**: 曲名は英語でわかりやすく付け直してください（例: `Midnight Rain Piano.mp3`）。ファイル名がそのまま動画のチャプター名になります。

---

## 4. ローカルで実行する（コマンド）

```bash
# 1. 依存ライブラリ（初回のみ）
pip install -r requirements.txt
# ffmpegが必要です（Mac: brew install ffmpeg / Ubuntu: sudo apt install ffmpeg）

# 2. .envを設定（.env.exampleをコピーして編集）
#    CLAUDE_API_KEY（メタデータ生成用）
#    YOUTUBE_CREDENTIALS_JSON（投稿用 → python setup_youtube_auth.py で取得）
#    STABILITY_API_KEY（背景画像生成用・任意。なくても動きます）

# 3. SunoのMP3を bgm_input/ に入れる

# 4. まずはドライラン（投稿せず動画だけ作って確認）
python bgm_pipeline.py --niche rain_sleep --hours 1 --dry-run

# 5. 問題なければ本番実行（YouTubeへ自動投稿）
python bgm_pipeline.py --niche rain_sleep --hours 1

# 慣れたら2〜3時間動画に（再生時間が貯まりやすい）
python bgm_pipeline.py --niche rain_sleep --hours 2
```

生成物は `output/bgm/<ニッチ>_<日時>/` に入ります（final.mp4 / thumbnail.jpg / metadata.json）。

---

## 5. GitHub Actionsで自動化する（PC不要）

1. GitHubリポジトリの **Settings → Secrets and variables → Actions** で以下を登録:
   - `CLAUDE_API_KEY`
   - `YOUTUBE_CREDENTIALS_JSON`
   - `STABILITY_API_KEY`（任意）
2. SunoのMP3を `bgm_input/` に入れて**コミット＆プッシュ**（GitHubのWeb画面から「Add file → Upload files」でもOK）
3. **Actions → 「BGM長尺動画 自動生成・投稿」→ Run workflow** で、ニッチ・時間・ドライランを選んで実行
4. ドライランの場合は生成された動画がアーティファクトとしてダウンロードできます

---

## 6. チャンネル運用の戦略（稼ぐための部分）

- **チャンネルは1ニッチに絞る**: 雨音睡眠チャンネルにLofiを混ぜない。YouTubeのおすすめアルゴリズムはチャンネルの一貫性を見ます。
- **投稿頻度**: 週2〜3本。Sunoでの曲作りは週1回30分まとめてやればOK。
- **タイトル/サムネは英語のみ**: このパイプラインが自動生成します。チャンネル名も英語に（例: `Rainfall Haven`, `Drift & Dream`, `The Quiet Library`）。
- **最初の1ヶ月は2時間動画を中心に**: 視聴1回あたりの再生時間が長く、4,000時間に最短で届きます。
- **公開時間**: 米国の夜に合わせる = **日本時間の朝9〜12時**に公開（米東部の20〜23時）。
- **再生リストを作る**: 「Sleep」「Study」などでまとめると連続再生が伸びます。
- **コメント返信**: 最初の100人の登録者がつくまでは全コメントに返信。アルゴリズム評価が上がります。

### 収益の目安
睡眠系のRPM $10〜25で、月50万回再生なら月$500〜1,250程度。最初の3ヶ月は収益ゼロが普通です（収益化条件を満たすまでの仕込み期間）。

---

## 7. トラブルシューティング

| 症状 | 対処 |
|---|---|
| `ffmpegが見つかりません` | `brew install ffmpeg`（Mac）/ `sudo apt install ffmpeg`（Linux） |
| `bgm_input/ に楽曲ファイルがありません` | SunoのMP3を `bgm_input/` に置く |
| 投稿がスキップされる | `.env` の `YOUTUBE_CREDENTIALS_JSON` を設定（`python setup_youtube_auth.py`） |
| 背景がグラデーションになる | `STABILITY_API_KEY` 未設定時の正常動作。設定するとAI画像になります |
| Content IDの申し立てが来た | Sunoの曲は稀に既存曲に似て誤検知されます。自分が権利者なので「異議申し立て」でほぼ解決します |

---

## 参考情報（調査ソース）

- [AI-Generated Music on YouTube: Monetization, RPM & Niches (2026) - OutlierKit](https://outlierkit.com/resources/ai-generated-music-youtube-monetization-2026/)
- [Suno Commercial Use: Free vs Pro Rights (2026) - Dynamoi](https://dynamoi.com/learn/ai-music-distribution/suno-commercial-rights-explained)
- [YouTube Music Monetization: YPP Thresholds (2026) - Dynamoi](https://dynamoi.com/learn/youtube-music-promotion/youtube-music-channel-monetization-requirements)
- [Top Trending Niches on YouTube 2026 - OutlierKit](https://outlierkit.com/blog/trending-niches-on-youtube)
- [YouTube channel monetization policies - YouTube Help](https://support.google.com/youtube/answer/1311392?hl=en)
