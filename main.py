# ────────────────────────────────────────────────────────────────
#   ADMIN GİRİŞ SAYFASI (VIP gibi basit ve çalışan hale getirildi)
# ────────────────────────────────────────────────────────────────

ADMIN_LOGIN_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Giriş</title>
    <style>
        body {background:#000;color:#fff;text-align:center;padding:80px 20px;font-family:sans-serif;}
        h2 {color:#0095f6;}
        input, button {padding:14px;font-size:17px;border-radius:8px;border:1px solid #444;}
        input {background:#111;color:#fff;width:90%;max-width:380px;}
        button {background:#0095f6;color:#fff;border:none;cursor:pointer;font-weight:bold;}
    </style>
</head>
<body>
    <h2>ADMIN PANEL GİRİŞ</h2><br>
    <form method="POST">
        <input type="password" name="p" placeholder="Admin Şifresi" required><br><br>
        <button type="submit">GİRİŞ YAP</button>
    </form>
</body>
</html>
"""

@app.route('/admin_giris', methods=['GET', 'POST'])
def admin_giris():
    if request.method == 'POST':
        girilen_sifre = request.form.get('p', '').strip()
        beklenen_sifre = SISTEM["admin_sifre"]
        
        # Hata ayıklama için log'a yaz (Render log'unda görünecek)
        print(f"[ADMIN GİRİŞ DENEMESİ] Girilen: '{girilen_sifre}' | Beklenen: '{beklenen_sifre}'")
        
        if girilen_sifre == beklenen_sifre:
            session['admin'] = True
            session.permanent = True  # session daha uzun süre kalsın
            print("[ADMIN] Giriş BAŞARILI")
            return redirect(url_for('admin'))
        else:
            print("[ADMIN] Giriş BAŞARISIZ")
            return '<h2 style="color:red;text-align:center;padding:100px;">YANLIŞ ŞİFRE!</h2>'
    
    return ADMIN_LOGIN_HTML
