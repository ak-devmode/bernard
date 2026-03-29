# Session Context — Broadcast Conversation History

**Dibuat:** 20 March 2026
**Status:** Siap dilanjutkan — menunggu keputusan desain sebelum implementasi

---

## Apa yang Sedang Dikerjakan

Menambahkan fitur agar **broadcast mencatat outbound message di Chatwoot conversation history**.

Saat ini ketika broadcast dikirim via modul Broadcasts di Chatwoot:
- Pesan sampai ke customer ✓
- Tercatat di `broadcast.sent_recipients` ✓
- **Tidak muncul di history chat / conversations** ✗

---

## Mengapa Tidak Muncul (Root Cause)

Di `app/services/whatsapp/broadcast_from_sheet_service.rb`, method `send_to`:

```ruby
message_id = channel.send_template(
  "+#{recipient[:phone]}",
  { name: name, namespace: namespace, ... },
  nil   # ← message parameter nil, tidak ada Message record dibuat
)

# Setelah berhasil:
sync_contact(recipient)  # hanya buat Contact, tidak buat Conversation
```

Tidak ada yang memanggil `ContactInboxWithContactBuilder` untuk buat `ContactInbox`, dan tidak ada `Conversation.create!`. Lihat dokumentasi lengkap di `pmg-docs/development/chatwoot-message-routing.md`.

---

## Solusi yang Akan Diimplementasikan

Tambah method `sync_conversation` di `broadcast_from_sheet_service.rb` dan panggil setelah `sync_contact`.

### Code yang akan ditambahkan

**Di method `send_to` (setelah `sync_contact` line ~143):**
```ruby
sync_contact(recipient)       # sudah ada
sync_conversation(recipient)  # ← tambah ini
```

**Method baru `sync_conversation`:**
```ruby
def sync_conversation(recipient)
  phone_e164 = "+#{recipient[:phone]}"

  contact_inbox = ::ContactInboxWithContactBuilder.new(
    inbox: inbox,
    contact_attributes: { name: recipient[:name], phone_number: phone_e164 }
  ).perform

  return unless contact_inbox

  # KEPUTUSAN DESAIN BELUM DITENTUKAN — lihat section di bawah
  conversation = contact_inbox.conversations.where.not(status: :resolved).last
  conversation ||= ::Conversation.create!(
    account_id:       broadcast.account_id,
    inbox_id:         inbox.id,
    contact_id:       contact_inbox.contact_id,
    contact_inbox_id: contact_inbox.id
  )

  template_name = broadcast.template_params['name'] || broadcast.title
  conversation.messages.create!(
    account_id:   broadcast.account_id,
    inbox_id:     inbox.id,
    message_type: :outgoing,
    content:      "[Broadcast] #{template_name}",
    status:       :sent
  )

  Rails.logger.info "[BROADCAST #{broadcast.id}] Conversation synced for #{phone_e164} (conversation: #{conversation.id})"
rescue StandardError => e
  Rails.logger.warn "[BROADCAST #{broadcast.id}] Gagal sync conversation #{recipient[:phone]}: #{e.message}"
end
```

---

## ✅ Keputusan Desain

**Opsi A dipilih** — broadcast message masuk ke conversation open yang sudah ada; buat baru hanya jika tidak ada.

---

## State Saat Ini

### Branch
- **Branch aktif:** `develop` (local dan remote sudah sync)
- PR #11 sudah merged ke develop
- Tidak ada uncommitted changes

### Fitur yang Sudah Selesai (di develop)
- [x] 6.1.1 Template list dari Meta API live
- [x] 6.2.1 Create template (submit ke Meta)
- [x] 6.2.2 Edit template (dialog info limitasi API)
- [x] 6.2.3 Save as draft
- [x] 6.2.4 Delete template (konfirmasi ketik "delete")
- [x] 6.2.5 Copy as new
- [x] 6.3.1 Broadcast detail per-recipient (Sent/Failed tabs)
- [x] 6.3.2 Sort failures to top (tab All)
- [x] 6.3.3 Status chips (teal = sent, ruby = failed)

### Fitur Berikutnya (broadcast conversation history)
- [x] Implementasi `sync_conversation` di `broadcast_from_sheet_service.rb` — selesai 20 March 2026
- [ ] Test lokal: kirim broadcast kecil → verifikasi conversation muncul di localhost:3000
- [ ] Push ke feature branch baru → PR → staging → production

---

## Cara Test Lokal

Development tidak menerima inbound dari Meta (tidak ada public URL). Tapi untuk fitur ini, kita hanya butuh **outbound** — broadcast dikirim dan conversation dibuat di DB.

1. Jalankan Docker: `cd "D:/2 - Padma/7 - Chatwoot/chatwoot" && docker compose up -d`
2. Buka `localhost:3000` → login → buka Broadcasts
3. Kirim broadcast kecil ke 1-2 nomor test (menggunakan Meta API credentials yang ada di .env)
4. Cek apakah conversation baru muncul di Conversations untuk nomor tersebut
5. Kalau muncul → implementasi berhasil → push ke feature branch

---

## File yang Akan Diubah

Hanya **1 file:**
- `app/services/whatsapp/broadcast_from_sheet_service.rb`

Perubahan minimal, low-risk, mudah di-revert dengan `git checkout`.

---

## Setup Lokal

- Docker compose: `cd "D:/2 - Padma/7 - Chatwoot/chatwoot" && docker compose up -d`
- Tunggu ~35 detik untuk Rails boot, lalu buka `localhost:3000`
- Build Vite pertama kali butuh ~8 menit (normal, selanjutnya tidak perlu build ulang)
- Vite dev server: port 3036 (berjalan otomatis via container)

## Server Production

- **Chatwoot prod**: `ssh -i "D:/2 - Padma/7 - Chatwoot/16_chatwoot_services.pem" ubuntu@10.10.3.112`
- App di: `/home/chatwoot/chatwoot/` — berjalan di Docker (bukan systemd)
- Containers: `chatwoot-web-production`, `chatwoot-sidekiq-production`
- Deploy via CI/CD: push ke `main` branch → `pmg-deploy.yml` otomatis build + deploy
