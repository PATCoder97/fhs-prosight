# 🔧 Quick Fix Guide - OAuth redirect_uri_mismatch

## 🐛 Vấn đề bạn đang gặp:

```
Error: redirect_uri_mismatch
Expected: https://hrsfhs.tphomelab.io.vn/api/auth/google/callback
Actual:   http://hrsfhs.tphomelab.io.vn/api/auth/google/callback ❌
```

Backend đang tạo redirect URI với HTTP thay vì HTTPS mặc dù bạn truy cập qua HTTPS.

---

## ✅ Giải pháp - 3 bước nhanh:

### **Bước 1: Deploy backend mới (có debug logging)**

GitHub Actions đang build backend image mới với debug logging để tìm nguyên nhân.

**Kiểm tra build status:**
```bash
# Truy cập: https://github.com/PATCoder97/fhs-prosight/actions
# Đợi build hoàn tất (~6 phút)
```

**Sau khi build xong, deploy:**

```bash
# SSH vào CasaOS server
ssh user@your-casaos-ip

# Pull image mới nhất
docker pull patcoder97/prosight-backend:dev

# Restart backend
docker restart tp75-api

# Hoặc dùng docker-compose
docker-compose -f docker-compose.prod.yml up -d --force-recreate tp75-api
```

---

### **Bước 2: Test OAuth và xem logs**

#### **A. Test OAuth login:**

1. Truy cập: `https://hrsfhs.tphomelab.io.vn/login`
2. Click "Đăng nhập với Google"
3. (Sẽ vẫn bị lỗi, nhưng sẽ có logs để debug)

#### **B. Xem backend logs để tìm nguyên nhân:**

```bash
# Xem logs real-time
docker logs tp75-api --tail 100 -f

# Hoặc chỉ xem OAuth logs
docker logs tp75-api --tail 200 | grep -A 10 "OAuth redirect_uri"
```

**Logs sẽ hiển thị:**

```
INFO: OAuth redirect_uri generation:
INFO:   Base URI: http://hrsfhs.tphomelab.io.vn/api/auth/google/callback
INFO:   X-Forwarded-Proto: https  ← Kiểm tra giá trị này!
INFO:   All headers: {...}
INFO:   ✓ Converted to HTTPS: https://hrsfhs.tphomelab.io.vn/api/auth/google/callback
```

**Hoặc nếu có vấn đề:**

```
WARNING:   ⚠ X-Forwarded-Proto not 'https', keeping original scheme
```

---

### **Bước 3: Fix dựa trên logs**

#### **Case 1: Logs hiển thị `X-Forwarded-Proto: None` hoặc không có**

**Nguyên nhân:** Cloudflare không forward header

**Fix - Cloudflare SSL/TLS Settings:**

1. Login Cloudflare Dashboard
2. Chọn domain `tphomelab.io.vn`
3. **SSL/TLS → Overview**
4. **Encryption mode:** Chuyển từ "Flexible" → **"Full"** hoặc **"Full (strict)"**

```
❌ Flexible:  Cloudflare ↔ Origin dùng HTTP (không forward X-Forwarded-Proto)
✅ Full:      Cloudflare ↔ Origin dùng HTTPS (forward X-Forwarded-Proto: https)
```

5. **SSL/TLS → Edge Certificates**
6. **Always Use HTTPS:** ON

7. **Đợi 5-10 phút** để Cloudflare cập nhật
8. Test lại OAuth

---

#### **Case 2: Logs hiển thị `X-Forwarded-Proto: http`**

**Nguyên nhân:** Cloudflare đang dùng HTTP đến origin server

**Fix:**

1. Cloudflare → SSL/TLS → Overview
2. Chuyển Encryption mode → **"Full (strict)"**
3. Test lại

---

#### **Case 3: Logs hiển thị `X-Forwarded-Proto: https` nhưng vẫn bị lỗi**

**Nguyên nhân:** Code backend không convert đúng

**Fix:** Kiểm tra code conversion logic:

```bash
# Xem logs chi tiết
docker logs tp75-api --tail 200 | grep -B 5 -A 10 "Converted to HTTPS"
```

Nếu thấy:
```
INFO:   ✓ Converted to HTTPS: https://hrsfhs.tphomelab.io.vn/api/auth/google/callback
```

Nhưng Google vẫn nhận HTTP → **Có thể là caching issue**

**Solution:**
```bash
# Restart toàn bộ stack
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# Clear browser cache
# DevTools → Application → Clear all
```

---

## 🔍 Additional Debugging

### **Debug 1: Kiểm tra Cloudflare forward headers**

```bash
# Test từ server
curl -I https://hrsfhs.tphomelab.io.vn/api/health

# Kiểm tra response headers có Cloudflare info không
# Expected: cf-ray, cf-cache-status, etc.
```

### **Debug 2: Test direct HTTP request đến backend**

```bash
# Test trực tiếp đến backend container (bypass Cloudflare)
docker exec tp75-api curl -v http://localhost:8001/api/health

# Test với X-Forwarded-Proto header
docker exec tp75-api curl -v \
  -H "X-Forwarded-Proto: https" \
  http://localhost:8001/api/auth/login/google
```

### **Debug 3: Kiểm tra backend có nhận đúng host không**

```bash
# Check environment variables
docker exec tp75-api printenv | grep -E "FRONTEND_URL|COOKIE_DOMAIN|COOKIE_SECURE"

# Expected:
# FRONTEND_URL=https://hrsfhs.tphomelab.io.vn
# COOKIE_SECURE=true
# COOKIE_DOMAIN=.tphomelab.io.vn (hoặc empty)
```

---

## 📋 Google Cloud Console - Add Redirect URIs

Trong khi chờ debug, hãy thêm cả HTTP và HTTPS redirect URIs vào Google Cloud Console:

**Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client IDs:**

```
Authorized redirect URIs:
✅ https://hrsfhs.tphomelab.io.vn/api/auth/google/callback
✅ http://hrsfhs.tphomelab.io.vn/api/auth/google/callback  (temporary fallback)
✅ http://localhost:8001/api/auth/google/callback
✅ http://127.0.0.1:8001/api/auth/google/callback
```

**Note:** Thay đổi có thể mất **5-30 phút** để Google cập nhật.

---

## 🎯 Expected Timeline:

1. **GitHub Actions build:** ~6 phút
2. **Deploy backend mới:** ~2 phút
3. **Test + xem logs:** ~1 phút
4. **Fix Cloudflare settings (nếu cần):** ~5 phút
5. **Cloudflare propagation:** ~5-10 phút
6. **Google OAuth update:** ~5-30 phút

**Total:** ~20-50 phút

---

## ✅ Success Checklist:

- [ ] Backend image mới deployed
- [ ] Logs hiển thị `X-Forwarded-Proto: https`
- [ ] Logs hiển thị `✓ Converted to HTTPS`
- [ ] Cloudflare SSL mode = "Full" hoặc "Full (strict)"
- [ ] Google Console có HTTPS redirect URI
- [ ] OAuth redirect thành công (không còn redirect_uri_mismatch)

---

## 📞 Nếu vẫn không work sau khi thử hết:

**Share logs với tôi:**

```bash
# Lấy logs backend
docker logs tp75-api --tail 200 > backend_logs.txt

# Upload logs hoặc paste vào chat
```

**Hoặc screenshot:**
- Cloudflare SSL/TLS settings
- Google Cloud Console OAuth redirect URIs
- Browser DevTools → Network tab (OAuth request)

---

**Last Updated:** 2026-01-14
**Build Trigger:** `48398b5` - Backend with OAuth debug logging
**Estimated Fix Time:** 20-50 minutes
