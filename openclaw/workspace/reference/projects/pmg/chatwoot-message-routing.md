# Chatwoot Message Routing — Complete Flow

**Author:** Alex + Claude
**Date:** 20 March 2026
**Purpose:** Menjelaskan alur lengkap pesan masuk, keluar, dan broadcast di Chatwoot + WhatsApp Meta Cloud API.

---

## Overview

Ada tiga jalur utama pesan dalam aplikasi ini:

| Jalur | Arah | Buat History Chat? |
|---|---|---|
| Outbound (agent reply) | Agent → Meta → Customer | ✓ Ya |
| Inbound (customer reply) | Customer → Meta → Chatwoot | ✓ Ya |
| Broadcast | Sheet → Meta → Customer | ✗ Tidak |

---

## 1. Outbound — Agent Kirim Pesan ke Customer

Ketika agent mengetik dan mengirim pesan di Chatwoot UI:

```
Chatwoot UI (agent ketik pesan)
  │
  ▼
POST /api/v1/accounts/conversations/{id}/messages
  → MessagesController#create
  │
  ▼
MessageBuilder
  → Buat record Message di DB
  → message_type: outgoing
  → status: pending
  │
  ▼
SendReplyJob (background via Sidekiq)
  │
  ▼
SendOnWhatsappService
  → Cek: apakah dalam 24-jam reply window?
  → Ya  → send_session_message (text biasa)
  → Tidak → send_template_message (template Meta)
  │
  ▼
WhatsappCloudService
  → HTTP POST ke Meta Cloud API
  → Endpoint: /{phone_number_id}/messages
  → Header: Authorization: Bearer {api_key}
  │
  ▼
Meta API → Customer WhatsApp
  │
  ▼
Meta kirim webhook balik ke Chatwoot
  → Update status message: sent → delivered → read
```

**File utama:**
- `app/controllers/api/v1/accounts/conversations/messages_controller.rb`
- `app/builders/messages/message_builder.rb`
- `app/jobs/send_reply_job.rb`
- `app/services/whatsapp/send_on_whatsapp_service.rb`
- `app/services/whatsapp/providers/whatsapp_cloud_service.rb`

---

## 2. Inbound — Customer Kirim Pesan ke Chatwoot

Ketika customer mengirim WhatsApp ke nomor kita:

```
Customer kirim pesan WhatsApp
  │
  ▼
Meta POST webhook ke /webhooks/whatsapp/{phone_number}
  → WhatsappController#process_payload
  → Verifikasi webhook token
  → Cek apakah nomor aktif
  │
  ▼
WhatsappEventsJob (background via Sidekiq)
  → Temukan channel dari payload (phone_number_id)
  │
  ▼
IncomingMessageBaseService
  │
  ├─ Jika payload = statuses
  │    → process_statuses()
  │    → Update status message yang sudah ada (sent/delivered/read/failed)
  │
  └─ Jika payload = messages
       │
       ▼
       ContactInboxWithContactBuilder
         → Cari Contact by phone_number
         → Jika tidak ada → buat Contact baru (nama dari profil WhatsApp)
         → Buat/temukan ContactInbox (link contact ↔ inbox)
       │
       ▼
       set_conversation()
         → Cari conversation open untuk contact ini
         → Jika tidak ada → buat Conversation baru
         → (Jika lock_to_single_conversation: pakai conversation terakhir)
       │
       ▼
       create_message()
         → Buat record Message di DB
         → message_type: incoming
         → sender: contact
         → source_id: Meta message ID
       │
       ▼
       ActionCable → notifikasi real-time ke agent di UI
```

**File utama:**
- `config/routes.rb` (baris ~577: webhook route)
- `app/controllers/webhooks/whatsapp_controller.rb`
- `app/jobs/webhooks/whatsapp_events_job.rb`
- `app/services/whatsapp/incoming_message_base_service.rb`
- `app/services/whatsapp/incoming_message_service_helpers.rb`
- `app/builders/contact_inbox_with_contact_builder.rb`

---

## 3. Broadcast — Kirim Massal dari Google Sheet

Ketika agent menjalankan broadcast dari modul Broadcasts:

```
Agent klik Send Broadcast di UI
  │
  ▼
POST /api/v1/accounts/broadcasts
  → BroadcastsController#create
  → Buat record Broadcast di DB (status: draft)
  → Queue job: BroadcastExecutorJob
  │
  ▼
BroadcastExecutorJob (background via Sidekiq)
  → Panggil BroadcastFromSheetService
  │
  ▼
BroadcastFromSheetService#perform
  → broadcast.processing!
  → Baca baris dari Google Sheet (GoogleSheetsService)
  → Terapkan filter (kolom/nilai dari template_params)
  → Normalisasi nomor HP (0xxx → 62xxx, 8xxx → 628xxx)
  │
  ▼
  Untuk setiap penerima → send_to(recipient)
    │
    ▼
    TemplateProcessorService
      → Ambil info template (nama, namespace, lang_code, parameters)
      → Map kolom sheet ke variabel template
    │
    ▼
    channel.send_template(phone, template_info, message: nil)
      → WhatsappCloudService
      → HTTP POST ke Meta Cloud API
      → Meta kirim ke HP customer
    │
    ▼
    Jika berhasil:
      → broadcast.increment!(:sent_count)
      → record_success → simpan ke broadcast.sent_recipients
      → sync_contact → buat/update Contact di Chatwoot (best-effort)
    │
    Jika gagal:
      → broadcast.increment!(:failed_count)
      → record_failure → simpan ke broadcast.failed_recipients (+ pesan error)
  │
  ▼
  broadcast.completed!
```

**File utama:**
- `app/controllers/api/v1/accounts/broadcasts_controller.rb`
- `app/jobs/broadcasts/broadcast_executor_job.rb`
- `app/services/whatsapp/broadcast_from_sheet_service.rb`
- `app/services/whatsapp/template_processor_service.rb`

---

## 4. Kenapa Broadcast Tidak Membuat History Chat

Ini adalah **keputusan arsitektur** — bukan bug. Ada tiga alasan teknis:

### Alasan 1: `message: nil`
```ruby
# broadcast_from_sheet_service.rb
channel.send_template(
  "+#{recipient[:phone]}",
  { name: name, namespace: namespace, ... },
  nil   # ← tidak ada Message record
)
```
Provider hanya mengirim HTTP ke Meta, tidak menyimpan apapun ke tabel `messages`.

### Alasan 2: Tidak ada `ContactInbox`
`sync_contact()` hanya membuat `Contact` (data kontak), bukan `ContactInbox` (link kontak ke inbox). Tanpa `ContactInbox`, tidak bisa ada `Conversation`.

### Alasan 3: Tidak ada `Conversation.create!`
Tidak ada satu pun titik di broadcast flow yang memanggil pembuat conversation.

### Akibat
- Pesan sampai ke customer ✓
- Meta menyimpan pengiriman ✓
- Chatwoot menyimpan hasil di `Broadcast.sent_recipients` ✓
- **Tidak ada di tabel `messages`** ✗
- **Tidak ada di tabel `conversations`** ✗

### Ketika Customer Membalas Broadcast
Ketika customer membalas pesan broadcast:
- Masuk lewat jalur **Inbound** (nomor 2 di atas)
- `IncomingMessageBaseService` membuat `ContactInbox` + `Conversation` + `Message` baru
- Conversation baru ini **tidak terhubung** ke broadcast asalnya
- Ini by design: broadcast bersifat satu arah

---

## 5. Diagram Ringkas

```
OUTBOUND (agent → customer):
  UI → Message(DB) → Job → Meta API → Customer
                                ↑
                    Status webhook balik (sent/delivered/read)

INBOUND (customer → agent):
  Customer → Meta webhook → Contact+ContactInbox+Conversation+Message(DB) → UI

BROADCAST (sheet → customer):
  Sheet → Job → Meta API → Customer
                           (tidak ada yang disimpan ke messages/conversations)
```

---

## 6. Tabel Data Utama

| Model | Tabel | Dibuat oleh |
|---|---|---|
| `Message` | `messages` | MessageBuilder (outbound), IncomingMessageBaseService (inbound) |
| `Conversation` | `conversations` | IncomingMessageBaseService, ConversationBuilder |
| `Contact` | `contacts` | ContactInboxWithContactBuilder, sync_contact (broadcast) |
| `ContactInbox` | `contact_inboxes` | ContactInboxWithContactBuilder (inbound only) |
| `Broadcast` | `broadcasts` | BroadcastsController |

---

## Edit Log

| Versi | Tanggal | Perubahan |
|---|---|---|
| 1.0 | 20 March 2026 | Initial — complete routing flow documentation |
