# web_project
網頁程式設計期末project

我把老師的Django範例檔下載然後再用boostrap的模板套上去，到時候可以重新選模板  
模板: https://startbootstrap.com/template/shop-homepage#google_vignette  
(這個網站是老師簡報給的只有找到一個購物網站的模板所以先隨便套一下)    
  
下載語法：
```bash
git clone https://github.com/Yingka10/web_project.git
cd web_project
```

要如何登入admin

GitHub Copilot: 要登入 Django Admin，請按照以下步驟操作：

---

### 1. **啟動開發伺服器**
在終端機中執行以下命令啟動伺服器：

```bash
python manage.py runserver
```

伺服器啟動後，訪問以下網址進入 Django Admin 登入頁面：

[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

### 2. **建立超級使用者**
如果您還沒有超級使用者帳號，請執行以下命令來建立：

```bash
python manage.py createsuperuser
```

系統會提示您輸入以下資訊：

1. **使用者名稱**：輸入您想要的管理員帳號名稱。
2. **電子郵件地址**：輸入有效的電子郵件地址（可選）。
3. **密碼**：輸入密碼，並再次確認。

完成後，系統會顯示訊息，確認超級使用者已建立。

---

### 3. **登入 Django Admin**
1. 打開瀏覽器，訪問 [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)。
2. 使用剛剛建立的超級使用者帳號和密碼登入。

---

### 4. **管理 `Post` 模型**
您已經在 admin.py 中註冊了 `Post` 模型：

```python
admin.site.register(Post)
```

登入後，您應該可以在 Django Admin 中看到 `Post` 模型，並可以新增、編輯或刪除商品資料。

