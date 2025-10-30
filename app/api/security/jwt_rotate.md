# JWT Rotation (K032)
- Access token 15 dk, refresh 7 gün.
- `kid` başlığı ile anahtar versiyonla; anahtar yenilemede eski anahtarı grace ile tut.
- Compromise senaryosunda kid revocation listesi.
