# AdSense × Site Kit by Google 連携手順

対象サイト: **https://yohaku-lab.net**
パブリッシャーID: **`pub-9232236779314485`**

このディレクトリは、`yohaku-lab.net`（WordPress 想定）に Google AdSense を Site Kit プラグイン経由で接続するための手順書とアセットをまとめたものです。
本リポジトリ（`auto-short-video`）は Python 製の動画自動生成パイプラインなので、Site Kit プラグイン本体は含みません。WordPress 側にプラグインを導入したうえで、本ディレクトリのアセットと手順を使ってください。

---

## 目次

1. [前提条件](#前提条件)
2. [Step 1. Site Kit プラグインの導入](#step-1-site-kit-プラグインの導入)
3. [Step 2. Site Kit の初回セットアップ（Search Console 接続）](#step-2-site-kit-の初回セットアップsearch-console-接続)
4. [Step 3. AdSense の接続（pub-9232236779314485）](#step-3-adsense-の接続pub-9232236779314485)
5. [Step 4. ads.txt の設置](#step-4-adstxt-の設置)
6. [Step 5. 自動広告の有効化と表示確認](#step-5-自動広告の有効化と表示確認)
7. [Step 6. AdSense 審査ステータスの確認](#step-6-adsense-審査ステータスの確認)
8. [付録 A. Site Kit を使えない場合のフォールバック（手動タグ）](#付録-a-site-kit-を使えない場合のフォールバック手動タグ)
9. [付録 B. トラブルシュート](#付録-b-トラブルシュート)

---

## 前提条件

- `yohaku-lab.net` が WordPress で運用されていること（管理画面 `https://yohaku-lab.net/wp-admin/` にアクセス可能）。
- WordPress 管理者ユーザーで、かつ Google AdSense オーナー（`pub-9232236779314485`）と同一の Google アカウントでログインできること。
- サイトが HTTPS で公開されており、Google にクロール可能（`robots.txt` で `Googlebot` をブロックしていない）。
- AdSense 側でサイト `yohaku-lab.net` が「審査中」または「準備完了」になっていること（共有された URL: <https://adsense.google.com/adsense/u/0/pub-9232236779314485/sites/detail/url=yohaku-lab.net>）。

---

## Step 1. Site Kit プラグインの導入

1. WordPress 管理画面 → **プラグイン** → **新規追加**
2. 検索ボックスで `Site Kit by Google` を検索
3. 提供元が **Google** の `Site Kit by Google`（公式）を **今すぐインストール** → **有効化**
4. 左メニューに **Site Kit** が表示されたことを確認

> WP-CLI が使える場合:
> ```bash
> wp plugin install google-site-kit --activate
> ```

---

## Step 2. Site Kit の初回セットアップ（Search Console 接続）

Site Kit は AdSense 単独では接続できず、まず Search Console を経由してサイトの所有確認を行います。

1. 左メニュー **Site Kit** → **Start setup**
2. 「Sign in with Google」 → **AdSense `pub-9232236779314485` を所有する Google アカウント**でログイン
3. Site Kit が要求するスコープに同意（`openid / email / profile / Search Console / Tag Manager` 系）
4. **Verify ownership of yohaku-lab.net** をクリック → 自動的に DNS / メタタグ方式で所有確認
5. **Allow Site Kit to place a tag on your site** に同意
6. **Set up Search Console** を完了
7. ダッシュボードに `yohaku-lab.net` が表示されれば OK

---

## Step 3. AdSense の接続（pub-9232236779314485）

1. **Site Kit** → **Settings** → **Connect more services**
2. **AdSense** の **Connect service** をクリック
3. Google ログイン画面で **同じアカウント**を選択（複数アカウントがある場合は注意）
4. AdSense アカウント選択画面で **`pub-9232236779314485`** を選ぶ
5. **「Place AdSense code」** に同意（Site Kit が自動で `<head>` に AdSense Auto Ads のスニペットを挿入します）
6. 接続完了後、`Site Kit > Settings > Connected Services > AdSense` に以下が表示されることを確認:
   - Publisher ID: `pub-9232236779314485`
   - Account status: `Ready` もしくは `Getting paid`（審査中の場合は `Pending`）

> Site Kit が挿入する AdSense タグはバージョン管理されており、テーマや子テーマを編集する必要はありません。

---

## Step 4. ads.txt の設置

`ads.txt` は AdSense 収益保護のための必須ファイルです。Site Kit でも警告として案内されます。

### 4-1. 本リポジトリのファイルを使う

このディレクトリに [`ads.txt`](./ads.txt) を用意済みです。内容:

```
google.com, pub-9232236779314485, DIRECT, f08c47fec0942fa0
```

### 4-2. アップロード方法（いずれか）

**A. WordPress プラグインで配信（推奨）**
- プラグイン `Ads.txt Manager`（10up 製）を導入
- 管理画面 **設定 → Ads.txt** に上記 1 行を貼り付けて保存
- `https://yohaku-lab.net/ads.txt` にアクセスして内容が表示されることを確認

**B. サーバーのドキュメントルートに直接配置**
- FTP / SSH で WordPress の公開ディレクトリ（通常 `public_html/` または `htdocs/`）直下に [`ads.txt`](./ads.txt) を設置
- パーミッション `644`
- 確認: `curl -I https://yohaku-lab.net/ads.txt` が `200 OK` を返すこと

### 4-3. AdSense 側の反映確認

- AdSense 管理画面 → **サイト** → `yohaku-lab.net` の `ads.txt` ステータスが **「承認済み」** になるまで最大 24 時間
- それまでは **「ads.txt の問題が見つかりました」** という警告が出ますが正常です

---

## Step 5. 自動広告の有効化と表示確認

1. AdSense 管理画面 → **広告** → **サイトごと** → `yohaku-lab.net` の **編集（鉛筆アイコン）**
2. **自動広告** を **オン** に
3. 必要に応じて以下を調整:
   - **広告フォーマット**: ディスプレイ / インフィード / 記事内 / アンカー / モバイル全画面
   - **広告掲載量**: 中（推奨スタート）
   - **除外領域**: ヘッダー直下 / フッター / 固定ページなど
4. **サイトに適用** をクリック
5. 反映まで **最大 1 時間**。`https://yohaku-lab.net` をシークレットウィンドウで開いて広告が表示されるか確認
   - 広告ブロッカーは無効化すること
   - 表示されない場合は `?google_force_show_ad=1` を URL に付けてプレビュー

---

## Step 6. AdSense 審査ステータスの確認

共有 URL <https://adsense.google.com/adsense/u/0/pub-9232236779314485/sites/detail/url=yohaku-lab.net> を開き、サイトステータスを確認:

| ステータス | 意味 | 次のアクション |
|---|---|---|
| `準備中 / Getting ready` | 審査中 | 何もしない。最大 2 週間待つ |
| `準備完了 / Ready` | 審査通過、配信中 | Step 5 で自動広告 ON 済みか確認 |
| `要対応 / Requires review` | 審査落ち | AdSense 通知メールを確認、サイト改善後に再申請 |

審査落ちでよくある原因:
- コンテンツ量が少ない（最低 30 ページ程度推奨）
- プライバシーポリシー / お問い合わせページが無い
- ナビゲーションが不十分
- 著作権侵害の疑いがある画像／引用

---

## 付録 A. Site Kit を使えない場合のフォールバック（手動タグ）

何らかの理由で Site Kit が使えない場合は、AdSense Auto Ads スニペットを手動で `<head>` に挿入します。
スニペットは [`auto-ads-head.html`](./auto-ads-head.html) にあります。

### 挿入方法

**方法 1. テーマの `header.php` に直接書く（非推奨：テーマ更新で消える）**

**方法 2. プラグイン経由（推奨）**
- `WPCode`（旧 Insert Headers and Footers）などを導入
- **設定 → WPCode → ヘッダーとフッター → ヘッダー** に [`auto-ads-head.html`](./auto-ads-head.html) の中身をペースト
- 保存

**方法 3. functions.php フック**
- 子テーマの `functions.php` に以下を追加:

```php
add_action( 'wp_head', function () {
    ?>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9232236779314485"
            crossorigin="anonymous"></script>
    <?php
}, 5 );
```

> ⚠️ Site Kit と手動タグの **両方を入れると二重配信になり AdSense ポリシー違反**です。どちらか一方だけにしてください。

---

## 付録 B. トラブルシュート

### B-1. Site Kit で AdSense が「No AdSense account found」と出る

- ログインしている Google アカウントを確認。AdSense オーナー（`pub-9232236779314485` を所有するアカウント）と一致しているか
- 一度 Site Kit から AdSense を **Disconnect** → ブラウザのシークレットウィンドウで再接続

### B-2. 広告が表示されない

1. ブラウザの DevTools で `view-source:https://yohaku-lab.net` を開き、`<head>` 内に
   `pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9232236779314485` が
   含まれているか確認
2. キャッシュプラグイン（WP Super Cache / W3 Total Cache / LiteSpeed Cache など）でキャッシュをパージ
3. CDN（Cloudflare 等）を使っている場合は **キャッシュ強制パージ + 開発モード ON** で再確認
4. 広告ブロッカー無効化、シークレットウィンドウで確認
5. AdSense 審査が `Getting ready` の間は表示されない

### B-3. ads.txt が「未検出」のまま

- `https://yohaku-lab.net/ads.txt` を直接開いて `google.com, pub-9232236779314485, DIRECT, f08c47fec0942fa0` が表示されるか
- WordPress のリライトルールで 404 になっていないか（`Ads.txt Manager` プラグインを使えば回避可能）
- 反映には最大 24 時間かかる

### B-4. Site Kit の認証が何度もループする

- ブラウザの Cookie / サードパーティ Cookie 制限を確認
- WordPress の URL（`設定 → 一般`）と AdSense 登録 URL（`https://yohaku-lab.net`）が **完全一致**しているか（末尾スラッシュ・`www` 有無）

---

## 連絡用チェックリスト

作業完了の確認に使ってください。

- [ ] Site Kit プラグインを有効化した
- [ ] Search Console との接続が完了した
- [ ] AdSense（`pub-9232236779314485`）と接続した
- [ ] `https://yohaku-lab.net/ads.txt` が 200 OK で表示される
- [ ] 自動広告を ON にした
- [ ] AdSense 管理画面でサイトステータスが `準備完了` もしくは `準備中` になっている
- [ ] サイトをシークレットウィンドウで開いて表示崩れが無い
