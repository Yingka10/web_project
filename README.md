# web_project
網頁程式設計期末project

現在的資料庫只有商品的，登入註冊的帳戶都還沒用，還有上傳商品也還沒用到資料庫  
商品分類也還沒調，這些就是個大概
  
下載語法：
```bash
git clone https://github.com/Yingka10/web_project.git
cd web_project
```
!!要先`pip install pillow`  才可以處理影像

---
當然可以！以下是一份專為你的 Django 團隊量身打造的 `README.md` 範本，說明如何安裝環境、設定 `.env`、啟動專案等等，清楚又好懂👇

---


# 🛍️ 二手交易平台專案

這是一個使用 Django 建立的校園二手交易平台，團隊協作開發中。歡迎你加入開發！

---

## 🚀 快速開始

### ✅ 1. 安裝套件

請先安裝必要的 Python 套件（建議使用虛擬環境）：

```bash
pip install -r requirements.txt
```

---

### 🔑 2. 設定環境變數 `.env`

請根據 `.env.example` 建立你自己的 `.env` 檔案：

```bash
cp .env.example .env
```

打開 `.env` 並填入資料，例如：

```env
DEBUG=True
SECRET_KEY=這邊請填佳穎的 secret key
DATABASE_URL=postgres://帳號:密碼@host:port/資料庫名稱
```

如果你是使用我們統一的雲端資料庫，請洽組長索取正確連線字串。

> ⚠️ `.env` 是機密檔案，**不要上傳到 GitHub！**

---

### 🛠️ 3. 執行資料庫遷移

確保你的資料庫有正確連線後，執行：

```bash
python manage.py migrate
```

---

### 🌐 4. 啟動本地伺服器

啟動開發伺服器：

```bash
python manage.py runserver
```

然後在瀏覽器打開 `http://127.0.0.1:8000` 即可進入網站！

---

## 📁 專案結構說明

```
your_project/
├── myproject/         ← Django 主設定檔
├── mywebsite/         ← 你開發的 App
├── templates/         ← HTML 樣板
├── static/            ← CSS / JS / 圖片
├── media/             ← 使用者上傳的圖片
├── .env               ← 環境變數（不上傳）
├── .env.example       ← 環境變數樣板（供參考）
├── manage.py
└── README.md
```

---

## 👥 團隊開發注意事項

- 請先 `git pull` 再開發，避免衝突
- 新增功能請開新 branch，測試後再合併
- 若資料庫有異動（models.py 改動），請一起分享 migration 指令！

---

## ❓常見問題

### 無法連到資料庫？
- 檢查 `.env` 裡的 `DATABASE_URL` 是否正確
- 是否已經跑 `migrate`

### 啟動時出現 `SECRET_KEY` 錯誤？
- 檢查 `.env` 是否有填入 `SECRET_KEY`
- `settings.py` 是否有正確讀取環境變數

