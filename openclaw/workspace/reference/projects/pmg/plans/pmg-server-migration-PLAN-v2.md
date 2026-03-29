# PMG Web Server Migration Plan
**CentOS 7 (x86_64) → Ubuntu 22.04 LTS (ARM64)**

---

**Status:** Draft
**Version:** 1.0
**Date:** 2026-03-18
**Owner:** @Alex
**Related Docs:** `pmg-server-migration-PLAN.md`

---

## 1. Context

### 1.1 Source Server

- **OS:** CentOS 7, x86_64
- **IP:** 10.10.3.7 (internal)
- **Web server:** Apache 2.4.6
- **PHP:** 8.1.20 via php-fpm (single pool, port 9000)
- **Database:** MySQL 8.0.33 (local)
- **SSL:** Terminated at AWS ALB — server serves HTTP only on port 80
- **DNS/routing:** All domains resolve via ALB, not directly to this box

### 1.2 Target Server

- **OS:** Ubuntu 22.04 LTS, ARM64
- **Web server:** Nginx (replacing Apache — clean rebuild)
- **PHP:** 8.1.x via php8.1-fpm
- **Database:** MySQL 8.0.x (local, same major version)
- **SSL:** Same ALB termination pattern — no certbot required on box

### 1.3 Migration Approach

Clean rebuild. Do not lift-and-shift. Configure each service from scratch on Ubuntu, import data, validate, then cut over DNS at ALB target group level.

---

## 2. Sites Inventory

| # | Domain | Type | Source Docroot | Target Docroot | DB | Notes |
|---|---|---|---|---|---|---|
| 1 | `pbmcgroup.com` | WordPress | `/var/www/html` | `/var/www/pbmcgroup.com/html` | `pbmcgroup` | PHP 8.1 |
| 2 | `padmacare.pbmcgroup.com` | External | n/a | n/a | n/a | Hosted by external vendor — DNS points to vendor, not this box. No migration required. |
| 3 | `webcam.pbmcgroup.com` | Static HTML/JS | `/var/www/webcam.pbmcgroup.com` | `/var/www/webcam.pbmcgroup.com` | none | Git clone from GitHub |

### 2.1 Explicitly Excluded

- `padmacare.pbmcgroup.com` vhost — hosted by external vendor, DNS does not point to this box, ghost vhost only. Do not recreate on new server.
- Napier HIS (JBoss/Wildfly at `/opt/JBOSS`, `/opt/wildfly-18.0.1.Final`) — decommissioned
- phpMyAdmin (`/home/whello/www/phpMyAdmin`) — security liability, not migrated
- `/home/whello/` directory contents — stale, not migrated
- Chatwoot services on this box — already migrated independently

---

## 3. Pre-Migration Tasks

### 3.1 Source Server

- [ ] 3.1.1 Verify DB dump is complete: `grep -c "INSERT INTO" ~/wordpress-dump.sql` — confirm non-zero
- [ ] 3.1.2 Confirm which WP install is canonical: `pbmcgroup.com` serves from `/var/www/html` — verify `/home/whello/www/html` is stale and unused
- [ ] 3.1.3 Export full WP content from `/var/www/html` (themes, plugins, uploads): `tar -czf ~/wp-content.tar.gz /var/www/html/wp-content/`
- [ ] 3.1.4 Copy `wp-config.php` from `/var/www/html/wp-config.php` — needed for salt keys
- [ ] 3.1.5 Confirm webcam app git remote is current: `cd /var/www/webcam.pbmcgroup.com && git status && git log --oneline -5`
- [ ] 3.1.6 Document all active cron jobs: `crontab -l && sudo crontab -l`
- [ ] 3.1.7 Note current Apache error/access log paths for reference during smoke testing

### 3.2 AWS / Infrastructure

- [ ] 3.2.1 Provision new Ubuntu 22.04 ARM64 instance (EC2 t4g or equivalent)
- [ ] 3.2.2 Assign same security groups as current box (port 80 from ALB only, port 22 from VPN)
- [ ] 3.2.3 Confirm ALB target group — note current registered target (CentOS box) for cutover
- [ ] 3.2.4 Add new instance to ALB target group as inactive (register but deregister after confirming health check setup)
- [ ] 3.2.5 Ensure new box has IAM instance profile if any S3/SSM access is needed
- [ ] 3.2.6 Transfer files to new box: `scp ~/wordpress-dump.sql ~/wp-content.tar.gz ubuntu@<new-box-ip>:~/`

---

## 4. New Server Setup

### 4.1 Base System

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y nginx mysql-server php8.1-fpm php8.1-mysql php8.1-xml \
  php8.1-curl php8.1-gd php8.1-mbstring php8.1-zip php8.1-intl \
  php8.1-bcmath php8.1-imagick git curl unzip
```

- [ ] 4.1.1 Run base install
- [ ] 4.1.2 Confirm PHP version: `php8.1 -v`
- [ ] 4.1.3 Confirm nginx: `nginx -v`
- [ ] 4.1.4 Confirm MySQL: `mysql --version`

### 4.2 Directory Structure

```bash
sudo mkdir -p /var/www/pbmcgroup.com/html
sudo mkdir -p /var/www/webcam.pbmcgroup.com
sudo chown -R www-data:www-data /var/www/
```

- [ ] 4.2.1 Create directory structure as above

---

## 5. Site 1 — pbmcgroup.com (WordPress)

### 5.1 Database

```bash
# Create DB and user
sudo mysql -e "CREATE DATABASE pbmcgroup CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER 'wordpress-user'@'localhost' IDENTIFIED BY 'DARV7zNYB7js!';"
sudo mysql -e "GRANT ALL PRIVILEGES ON pbmcgroup.* TO 'wordpress-user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# Import dump
sudo mysql pbmcgroup < ~/wordpress-dump.sql
```

- [ ] 5.1.1 Create database `pbmcgroup`
- [ ] 5.1.2 Import dump — verify row counts post-import: `sudo mysql -e "SELECT COUNT(*) FROM pbmcgroup.wp_posts;"`
- [ ] 5.1.3 Confirm siteurl in DB: `sudo mysql -e "SELECT option_value FROM pbmcgroup.wp_options WHERE option_name='siteurl';"`

### 5.2 WordPress Files

```bash
cd /var/www/pbmcgroup.com/html
sudo tar -xzf ~/wp-content.tar.gz --strip-components=3
# Or fresh WP core download:
sudo curl -O https://wordpress.org/latest.tar.gz
sudo tar -xzf latest.tar.gz --strip-components=1
sudo rm latest.tar.gz
# Then restore wp-content from backup
sudo tar -xzf ~/wp-content.tar.gz -C /var/www/pbmcgroup.com/html/
sudo chown -R www-data:www-data /var/www/pbmcgroup.com/
```

- [ ] 5.2.1 Install WP core files
- [ ] 5.2.2 Restore `wp-content/` from backup (themes, plugins, uploads)
- [ ] 5.2.3 Create `wp-config.php` — update `DB_NAME` to `pbmcgroup`, copy salt keys from old config

**wp-config.php key changes:**
```php
define( 'DB_NAME', 'pbmcgroup' );
define( 'DB_USER', 'wordpress-user' );
define( 'DB_PASSWORD', 'DARV7zNYB7js!' );
define( 'DB_HOST', 'localhost' );
define( 'WP_HOME', 'https://pbmcgroup.com' );
define( 'WP_SITEURL', 'https://pbmcgroup.com' );
```

- [ ] 5.2.4 Update wp-config.php with above values + original salt keys

### 5.3 PHP-FPM Pool

Create `/etc/php/8.1/fpm/pool.d/pbmcgroup.conf`:

```ini
[pbmcgroup]
user = www-data
group = www-data
listen = /run/php/php8.1-fpm-pbmcgroup.sock
listen.owner = www-data
listen.group = www-data
pm = dynamic
pm.max_children = 10
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 3
```

- [ ] 5.3.1 Create pool config file
- [ ] 5.3.2 Restart php-fpm: `sudo systemctl restart php8.1-fpm`
- [ ] 5.3.3 Confirm socket exists: `ls /run/php/php8.1-fpm-pbmcgroup.sock`

### 5.4 Nginx Vhost

Create `/etc/nginx/sites-available/pbmcgroup.com`:

```nginx
server {
    listen 80;
    server_name pbmcgroup.com www.pbmcgroup.com;
    root /var/www/pbmcgroup.com/html;
    index index.php index.html;

    access_log /var/log/nginx/pbmcgroup.com.access.log;
    error_log  /var/log/nginx/pbmcgroup.com.error.log;

    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    location ~ \.php$ {
        include fastcgi_params;
        fastcgi_pass unix:/run/php/php8.1-fpm-pbmcgroup.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    }

    location ~ /\.ht {
        deny all;
    }

    location = /xmlrpc.php {
        deny all;
    }
}
```

- [ ] 5.4.1 Create vhost file
- [ ] 5.4.2 Enable: `sudo ln -s /etc/nginx/sites-available/pbmcgroup.com /etc/nginx/sites-enabled/`
- [ ] 5.4.3 Test config: `sudo nginx -t`
- [ ] 5.4.4 Reload: `sudo systemctl reload nginx`

---

## 6. Site 2 — webcam.pbmcgroup.com (Static)

### 6.1 Deploy

```bash
cd /var/www
sudo git clone git@github.com:fajrikalpa29/padma-webcam.git webcam.pbmcgroup.com
sudo chown -R www-data:www-data /var/www/webcam.pbmcgroup.com
```

- [ ] 6.1.1 Ensure deploy SSH key is on new box and has read access to `fajrikalpa29/padma-webcam`
- [ ] 6.1.2 Clone repo
- [ ] 6.1.3 Confirm files present: `ls /var/www/webcam.pbmcgroup.com/` — expect `index.html`, `app.js`, `styles.css`, `img/`

### 6.2 Nginx Vhost

Create `/etc/nginx/sites-available/webcam.pbmcgroup.com`:

```nginx
server {
    listen 80;
    server_name webcam.pbmcgroup.com;
    root /var/www/webcam.pbmcgroup.com;
    index index.html;

    access_log /var/log/nginx/webcam.pbmcgroup.com.access.log;
    error_log  /var/log/nginx/webcam.pbmcgroup.com.error.log;

    location / {
        try_files $uri $uri/ =404;
    }

    # Allow camera access over HTTP (required for getUserMedia in some browsers)
    add_header Permissions-Policy "camera=*";
    add_header Cross-Origin-Opener-Policy "same-origin";
    add_header Cross-Origin-Embedder-Policy "require-corp";
}
```

> **Note:** Browser `getUserMedia()` (webcam API) requires either HTTPS or localhost. Since SSL terminates at ALB, the browser sees HTTPS — this should work. If the app breaks on the new box, check that ALB is forwarding `X-Forwarded-Proto: https` and the app is reading it correctly.

- [ ] 6.2.1 Create vhost file
- [ ] 6.2.2 Enable and reload nginx
- [ ] 6.2.3 Test webcam functionality end-to-end before cutover — do not cut over this subdomain without a live camera test

---

## 7. Site 3 — padmacare.pbmcgroup.com (Future Migration — Separate Cutover)

> **Status:** Not in scope for current migration. Document only. Revisit when timeline confirmed.
>
> **Current state:** Hosted by Whello (design agency) on their own infrastructure. Whello has full server access and WP admin access. Domain stays as `padmacare.pbmcgroup.com`. DNS cutover will be the trigger for go-live on new box.

### 7.1 Pre-Migration Requirements (coordinate with Whello)

- [ ] 7.1.1 Confirm with Whello they can provide: full DB dump + `wp-content/` export + `wp-config.php` (or at minimum salt keys)
- [ ] 7.1.2 Get active plugin list from WP admin → Plugins — note any premium/licensed plugins that need re-activation on new host
- [ ] 7.1.3 Get active theme from WP admin → Appearance → Themes — note page builder in use (Elementor, Divi, Oxygen etc) — this affects whether XML export is sufficient or full DB is required
- [ ] 7.1.4 Confirm Whello retains WP admin access post-migration (add their user to new install, do not rely on old host credentials)
- [ ] 7.1.5 Check for any Whello-hosted dependencies (fonts, APIs, CDN assets) that may break on cutover

### 7.2 Database

```bash
sudo mysql -e "CREATE DATABASE padmacare CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER 'padmacare-user'@'localhost' IDENTIFIED BY '<generate-strong-password>';"
sudo mysql -e "GRANT ALL PRIVILEGES ON padmacare.* TO 'padmacare-user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
sudo mysql padmacare < ~/padmacare-dump.sql
sudo mysql -e "UPDATE padmacare.wp_options SET option_value='https://padmacare.pbmcgroup.com' WHERE option_name IN ('siteurl','home');"
```

- [ ] 7.2.1 Obtain DB dump from Whello (`padmacare-dump.sql`)
- [ ] 7.2.2 Create DB and import
- [ ] 7.2.3 Verify siteurl updated correctly
- [ ] 7.2.4 Store DB password in SSM under `/pmg/padmacare/db_password`

### 7.3 WordPress Files

```bash
cd /var/www/padmacare.pbmcgroup.com/html
sudo curl -O https://wordpress.org/latest.tar.gz
sudo tar -xzf latest.tar.gz --strip-components=1
sudo rm latest.tar.gz
# Restore wp-content from Whello export
sudo tar -xzf ~/padmacare-wp-content.tar.gz -C /var/www/padmacare.pbmcgroup.com/html/
sudo chown -R www-data:www-data /var/www/padmacare.pbmcgroup.com/
```

- [ ] 7.3.1 Install WP core (match version currently running on Whello's server — check WP admin → Dashboard → Updates)
- [ ] 7.3.2 Restore `wp-content/` from Whello export
- [ ] 7.3.3 Create `wp-config.php`:

```php
define( 'DB_NAME', 'padmacare' );
define( 'DB_USER', 'padmacare-user' );
define( 'DB_PASSWORD', '<from-ssm>' );
define( 'DB_HOST', 'localhost' );
define( 'WP_HOME', 'https://padmacare.pbmcgroup.com' );
define( 'WP_SITEURL', 'https://padmacare.pbmcgroup.com' );
```

- [ ] 7.3.4 Copy salt keys from Whello's `wp-config.php` (keeps existing login sessions valid) or generate fresh ones at https://api.wordpress.org/secret-key/1.1/salt/

### 7.4 PHP-FPM Pool

Create `/etc/php/8.1/fpm/pool.d/padmacare.conf`:

```ini
[padmacare]
user = www-data
group = www-data
listen = /run/php/php8.1-fpm-padmacare.sock
listen.owner = www-data
listen.group = www-data
pm = dynamic
pm.max_children = 10
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 3
```

- [ ] 7.4.1 Create pool config
- [ ] 7.4.2 Restart php-fpm: `sudo systemctl restart php8.1-fpm`

### 7.5 Nginx Vhost

Create `/etc/nginx/sites-available/padmacare.pbmcgroup.com`:

```nginx
server {
    listen 80;
    server_name padmacare.pbmcgroup.com;
    root /var/www/padmacare.pbmcgroup.com/html;
    index index.php index.html;

    access_log /var/log/nginx/padmacare.pbmcgroup.com.access.log;
    error_log  /var/log/nginx/padmacare.pbmcgroup.com.error.log;

    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    location ~ \.php$ {
        include fastcgi_params;
        fastcgi_pass unix:/run/php/php8.1-fpm-padmacare.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    }

    location ~ /\.ht {
        deny all;
    }

    location = /xmlrpc.php {
        deny all;
    }
}
```

- [ ] 7.5.1 Create vhost file
- [ ] 7.5.2 Enable: `sudo ln -s /etc/nginx/sites-available/padmacare.pbmcgroup.com /etc/nginx/sites-enabled/`
- [ ] 7.5.3 Test: `sudo nginx -t && sudo systemctl reload nginx`

### 7.6 Pre-Cutover Validation

Test against new box using `/etc/hosts` override before touching DNS:

- [ ] 7.6.1 Homepage loads correctly, visual design intact
- [ ] 7.6.2 WP admin login works (`/wp-admin`)
- [ ] 7.6.3 All pages load — check a sample of key pages
- [ ] 7.6.4 Images/media load (confirms wp-content/uploads migrated)
- [ ] 7.6.5 Any contact forms or GravityForms work and submit correctly
- [ ] 7.6.6 Confirm Whello admin user account exists and can log in
- [ ] 7.6.7 Check error log is clean: `sudo tail -50 /var/log/nginx/padmacare.pbmcgroup.com.error.log`

### 7.7 Cutover

- [ ] 7.7.1 Notify Whello of cutover window — they should be available in case of issues
- [ ] 7.7.2 Update ALB target group or DNS to point `padmacare.pbmcgroup.com` to new box
- [ ] 7.7.3 Confirm site loads via public DNS post-cutover
- [ ] 7.7.4 Ask Whello to confirm their admin access still works post-cutover
- [ ] 7.7.5 Agree with Whello on decommission timeline for their hosted copy

---

## 8. Nginx Global Config Hardening

- [ ] 8.1 Disable default nginx site: `sudo rm /etc/nginx/sites-enabled/default`
- [ ] 8.2 Set `server_tokens off;` in `/etc/nginx/nginx.conf`
- [ ] 8.3 Add `client_max_body_size 64M;` in http block (WP media uploads)
- [ ] 8.4 Confirm `www-data` user in `/etc/nginx/nginx.conf`

---

## 9. Pre-Cutover Validation

Run all checks against new box IP directly (bypassing ALB) using `/etc/hosts` override on local machine:

```
<new-box-ip>  pbmcgroup.com www.pbmcgroup.com
<new-box-ip>  webcam.pbmcgroup.com
```

### 9.1 pbmcgroup.com

- [ ] 9.1.1 Homepage loads, no PHP errors
- [ ] 9.1.2 WP admin login works (`/wp-admin`)
- [ ] 9.1.3 A post/page loads correctly
- [ ] 9.1.4 Media images load (confirms wp-content/uploads migrated)
- [ ] 9.1.5 Check error log is clean: `sudo tail -50 /var/log/nginx/pbmcgroup.com.error.log`

### 9.2 webcam.pbmcgroup.com

- [ ] 9.2.1 `index.html` loads
- [ ] 9.2.2 Camera permission prompt appears
- [ ] 9.2.3 Photo capture and background overlay works end-to-end
- [ ] 9.2.4 Test from clinical app context — confirm photo is received correctly by the calling app

### 9.3 ARM Compatibility

- [ ] 9.3.1 Check for any WP plugins using native PHP extensions with compiled binaries — run `php8.1 -m` and compare against plugin requirements
- [ ] 9.3.2 Check ImageMagick is ARM-compatible: `php8.1 -r "echo (extension_loaded('imagick') ? 'ok' : 'missing') . PHP_EOL;"`
- [ ] 9.3.3 Confirm MySQL client libraries are ARM builds: `mysql --version`

---

## 10. Cutover

- [ ] 10.1 Take final DB dump from CentOS box immediately before cutover
- [ ] 10.2 Import final dump delta to new box (or accept small data loss window if site is low-traffic)
- [ ] 10.3 In AWS ALB target group: register new Ubuntu box, deregister CentOS box
- [ ] 10.4 Confirm ALB health check passes on new box (HTTP 200 on `/`)
- [ ] 10.5 Monitor nginx error logs for 30 minutes post-cutover: `sudo tail -f /var/log/nginx/*.error.log`
- [ ] 10.6 Confirm both sites load correctly via public DNS
- [ ] 10.7 Remove `/etc/hosts` override from local machine and re-test

---

## 11. Post-Migration

- [ ] 11.1 Keep CentOS box running for 7 days post-cutover — do not terminate immediately
- [ ] 11.2 After 7 days with no issues: snapshot CentOS EBS volume, then terminate instance
- [ ] 11.3 Update any internal documentation referencing the old server IP
- [ ] 11.4 Confirm `webhook.pbmcgroup.com` DNS entry is removed or redirected if no longer needed
- [ ] 11.5 Review WP plugin update status on pbmcgroup.com — don't update during migration week

---

## 12. Open Questions

1. **webcam app — calling app integration** — confirm the clinical app that calls `webcam.pbmcgroup.com` uses the domain (not the IP) so cutover is transparent. @Alex to verify with app team.
2. **DB password rotation** — current WP DB password (`DARV7zNYB7js!`) is in plaintext in `wp-config.php` on the old box. Rotate after migration and store new value in SSM under `/pmg/pbmcgroup/db_password`. @Alex.
3. **`fajrikalpa29` GitHub account access** — confirm deploy SSH key is available on new box before migration day. @Alex.
4. **padmacare.pbmcgroup.com migration timing** — coordinate with Whello for DB dump + wp-content export. Separate cutover, timeline TBD. @Alex to initiate conversation with Whello when ready.

---

*Keywords: server migration, CentOS, Ubuntu, ARM, WordPress, nginx, Apache, pbmcgroup, padmacare, webcam*
