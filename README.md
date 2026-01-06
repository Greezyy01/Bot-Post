# Bot-Post
Bot Auto Post Discord dengan dashboard interaktif dan slash commands.

## Struktur
```
autopost-bot/
├── main.py
├── config.py
├── dashboard.py
├── scheduler.py
├── commands.py
├── models.py
├── utils.py
├── logs/
├── backups/
└── config.json
```

## Requirements
Lihat `autopost-bot/requirements.txt`.

## Cara Run di CMD (Windows / Linux / macOS)
1. Masuk ke folder repo:
   ```bash
   cd /path/ke/Bot-Post
   ```
2. Buat virtual env (opsional tapi direkomendasikan):
   ```bash
   python -m venv .venv
   ```
3. Aktifkan virtual env:
   - Windows (CMD):
     ```bat
     .venv\Scripts\activate
     ```
   - Windows (PowerShell):
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```
4. Install dependencies:
   ```bash
   pip install -r autopost-bot/requirements.txt
   ```
5. Set token bot (pilih salah satu):
   - Lewat environment variable:
     - Windows (CMD):
       ```bat
       set BOT_TOKEN=YOUR_TOKEN_HERE
       ```
     - Windows (PowerShell):
       ```powershell
       $env:BOT_TOKEN="YOUR_TOKEN_HERE"
       ```
     - macOS/Linux:
       ```bash
       export BOT_TOKEN="YOUR_TOKEN_HERE"
       ```
   - Atau gunakan `/setup` setelah bot online (token akan disimpan ke `config.json`).
6. Jalankan bot:
   ```bash
   python autopost-bot/main.py
   ```

## Slash Commands
- `/setup` - Setup awal bot via modal
- `/dashboard` - Dashboard monitoring
- `/stats` - Statistik bot
- `/quickadd` - Tambah channel cepat
- `/start` / `/stop` - Mulai/hentikan posting
- `/config` - Lihat pengaturan
