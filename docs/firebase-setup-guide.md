# Firebase Setup Guide — Complete Project Configuration

> **Target:** Firebase Realtime Database + Authentication for Water Meter Project  
> **Project Type:** IoT with ESP32 (edge) + Raspberry Pi (backend)  
> **Auth Method:** Email/Password (used by both ESP32 and RPi Pyrebase4)

---

## Table of Contents

1. [Create Firebase Project](#create-firebase-project)
2. [Enable Realtime Database](#enable-realtime-database)
3. [Configure Authentication](#configure-authentication)
4. [Create ESP32/RPi User Account](#create-esp32rpi-user-account)
5. [Get Web App Config (for Pyrebase4)](#get-web-app-config-for-pyrebase4)
6. [Set Security Rules](#set-security-rules)
7. [Database Structure Initialization](#database-structure-initialization)
8. [Service Account (Optional - Admin SDK)](#service-account-optional---admin-sdk)
9. [Firebase Console Tour](#firebase-console-tour)
10. [Pricing & Limits](#pricing--limits)
11. [Troubleshooting](#troubleshooting)

---

## Create Firebase Project

### Step-by-Step

1. Go to **[Firebase Console](https://console.firebase.google.com/)**
2. Click **Create a project** or **Add project**
3. **Project name:** `water-meter-leak-detection` (or your choice)
4. **Google Analytics:** Disable (not needed for this project)
   - Toggle OFF "Enable Google Analytics for this project"
5. Click **Create project**
6. Wait for provisioning (~30 seconds), then click **Continue**

> 📸 **Screenshot Placeholder:** *Firebase Console - Create Project dialog with project name filled in*

### Project ID Note

- Your project gets a unique **Project ID** (e.g., `water-meter-leak-detection-abc123`)
- This becomes part of your database URL: `https://<project-id>-default-rtdb.<region>.firebasedatabase.app`
- Note this ID for configuration

---

## Enable Realtime Database

1. In left sidebar: **Build** → **Realtime Database**
2. Click **Create Database**
3. **Location:** Choose closest to you
   - Philippines/SE Asia: `asia-southeast1` (Singapore)
   - US West: `us-west1`
   - Europe: `europe-west1`
4. **Security Rules:** Start in **Test Mode**
   - This allows read/write without auth during development
   - **We will secure it later** (see Security Rules section)
5. Click **Enable**

> 📸 **Screenshot Placeholder:** *Realtime Database creation dialog showing location selection and test mode*

### Database URL

After creation, note your **Database URL** (at top of Data tab):
```
https://water-meter-leak-detection-abc123-default-rtdb.asia-southeast1.firebasedatabase.app
```

This is your `FIREBASE_DATABASE_URL` for ESP32 config.

---

## Configure Authentication

### Enable Email/Password Provider

1. Left sidebar: **Build** → **Authentication**
2. Click **Get started** (if first time) or **Sign-in method** tab
3. Click **Email/Password**
4. Toggle **Enable** → **Save**
5. (Optional) Enable **Email link (passwordless sign-in)** — not used in this project

> 📸 **Screenshot Placeholder:** *Authentication → Sign-in method tab with Email/Password enabled*

### Authorized Domains (for Web Dashboard)

1. In Authentication → **Settings** tab → **Authorized domains**
2. Add your domains:
   - `localhost` (for local development)
   - `yourdomain.duckdns.org` (for remote access via DDNS)
   - `yourdomain.com` (if using custom domain)
3. Save

---

## Create ESP32/RPi User Account

### Create Dedicated Service User

1. Authentication → **Users** tab
2. Click **Add user**
3. **Email:** `esp32@your-project.iam.gserviceaccount.com`
   - Format: `<device-name>@<project-id>.iam.gserviceaccount.com`
   - Example: `esp32@water-meter-leak-detection-abc123.iam.gserviceaccount.com`
4. **Password:** Generate strong password (20+ chars)
   - Example: `WmLd@2026!SecurePass#ESP32`
   - **Save this password securely** — needed in ESP32 config.h and RPi .env
5. Click **Add user**

> 📸 **Screenshot Placeholder:** *Add User dialog with service account email format*

### Verify User Creation

- User appears in list with UID (e.g., `a1b2c3d4-e5f6-7890-abcd-ef1234567890`)
- This UID is used in security rules as `auth.uid`

### Create Second User for RPi (Optional but Recommended)

1. Add another user:
   - **Email:** `rpi-backend@your-project.iam.gserviceaccount.com`
   - **Password:** Different strong password
2. This allows separate credentials for RPi backend

---

## Get Web App Config (for Pyrebase4)

### Register Web App

1. Project Settings (gear icon ⚙️) → **General** tab
2. Scroll to **Your apps** section
3. Click **Web app** icon (`</>`)
4. **App nickname:** `water-meter-rpi`
5. Check **Also set up Firebase Hosting** → No (optional)
6. Click **Register app**

### Copy Config Object

```javascript
// This is what you'll copy:
const firebaseConfig = {
  apiKey: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  authDomain: "water-meter-leak-detection-abc123.firebaseapp.com",
  databaseURL: "https://water-meter-leak-detection-abc123-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "water-meter-leak-detection-abc123",
  storageBucket: "water-meter-leak-detection-abc123.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abcdef1234567890"
};
```

### Save as `firebase_config.json`

Create this file in your RPi project (`rpi/firebase_config.json`):

```json
{
  "apiKey": "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "authDomain": "water-meter-leak-detection-abc123.firebaseapp.com",
  "databaseURL": "https://water-meter-leak-detection-abc123-default-rtdb.asia-southeast1.firebasedatabase.app",
  "projectId": "water-meter-leak-detection-abc123",
  "storageBucket": "water-meter-leak-detection-abc123.appspot.com",
  "messagingSenderId": "123456789012",
  "appId": "1:123456789012:web:abcdef1234567890"
}
```

> ⚠️ **Important:** Add `firebase_config.json` to `.gitignore` — never commit to Git!

> 📸 **Screenshot Placeholder:** *Project Settings → General → Web App config displayed*

---

## Set Security Rules

### Development Rules (Test Mode - Open)

```json
{
  "rules": {
    ".read": true,
    ".write": true
  }
}
```

**Use only during initial development!** Change before deploying.

### Production Rules (Recommended)

Go to Realtime Database → **Rules** tab, replace with:

```json
{
  "rules": {
    "readings": {
      "$device_id": {
        "$timestamp": {
          ".read": "auth != null && auth.uid == $device_id",
          ".write": "auth != null && auth.uid == $device_id",
          ".validate": "newData.hasChildren(['inlet', 'fixture_1', 'fixture_2', 'fixture_3'])"
        }
      }
    },
    "commands": {
      "$device_id": {
        ".read": "auth != null && auth.uid == $device_id",
        ".write": "auth.uid == 'rpi-backend-uid' || auth.uid == 'dashboard-admin-uid'"
      }
    },
    "alerts": {
      "$device_id": {
        ".read": "auth != null",
        ".write": "auth.uid == 'rpi-backend-uid' || auth.uid == $device_id"
      }
    },
    "devices": {
      ".read": "auth != null",
      "$device_id": {
        ".write": "auth.uid == $device_id || auth.uid == 'dashboard-admin-uid'"
      }
    },
    "models": {
      ".read": "auth != null",
      ".write": "auth.uid == 'rpi-backend-uid'"
    },
    "config": {
      "$device_id": {
        ".read": "auth != null && auth.uid == $device_id",
        ".write": "auth.uid == 'dashboard-admin-uid'"
      }
    }
  }
}
```

### Get UIDs for Rules

1. Authentication → Users tab
2. Copy UID for each user:
   - `esp32@...` → `esp32-uid`
   - `rpi-backend@...` → `rpi-backend-uid`
   - Dashboard admin (if created) → `dashboard-admin-uid`
3. Replace placeholder UIDs in rules above

### Test Rules

Use **Rules Playground** (in Rules tab):
1. Simulate read/write as specific UID
2. Test paths: `/readings/wm_001/...`, `/commands/wm_001/...`
3. Verify allowed/denied as expected

> 📸 **Screenshot Placeholder:** *Rules Playground showing simulation results*

---

## Database Structure Initialization

### Manual Creation (Optional - Auto-created on first write)

You can pre-create the structure in Firebase Console → Data tab:

```json
{
  "readings": {
    "wm_001": {}
  },
  "commands": {
    "wm_001": {}
  },
  "alerts": {
    "wm_001": {}
  },
  "devices": {
    "wm_001": {
      "name": "Ground Floor Water Meter",
      "location": "Quezon Province",
      "sensors": [
        {"id": 0, "name": "inlet", "fixture": "main_inlet", "pin": 26},
        {"id": 1, "name": "fix1", "fixture": "bidet", "pin": 25},
        {"id": 2, "name": "fix2", "fixture": "kitchen", "pin": 33},
        {"id": 3, "name": "fix3", "fixture": "bathroom_shower", "pin": 32}
      ],
      "status": {
        "online": false,
        "last_seen": null,
        "firmware": "v2.1.0",
        "total_readings": 0,
        "active_alerts": 0
      },
      "config": {
        "upload_interval_seconds": 5,
        "pulse_per_liter_inlet": 450,
        "pulse_per_liter_fix1": 450,
        "pulse_per_liter_fix2": 450,
        "pulse_per_liter_fix3": 450,
        "leak_confirm_count": 3,
        "continuous_flow_minutes": 30,
        "confidence_threshold": 0.80,
        "alert_notification": true,
        "auto_shutoff": false,
        "night_mode_quiet": false
      },
      "created_at": "2026-07-14T00:00:00Z"
    }
  },
  "models": {
    "metadata": {
      "active_xgboost": "xgboost_v2",
      "active_isolation_forest": "iforest_v1",
      "last_trained": "2026-07-14T00:00:00Z",
      "accuracy": 96.2,
      "training_samples": 50000
    }
  },
  "config": {
    "wm_001": {
      "upload_interval_seconds": 5,
      "pulse_per_liter_inlet": 450,
      "pulse_per_liter_fix1": 450,
      "pulse_per_liter_fix2": 450,
      "pulse_per_liter_fix3": 450,
      "leak_confirm_count": 3,
      "continuous_flow_minutes": 30,
      "confidence_threshold": 0.80,
      "alert_notification": true,
      "auto_shutoff": false,
      "night_mode_quiet": false
    }
  }
}
```

### Let ESP32 Create Structure (Simpler)

Just start the ESP32 — it will create `/readings/wm_001/...` automatically on first upload.

---

## Service Account (Optional - Admin SDK)

> **Only needed if using `firebase-admin` Python SDK on RPi instead of Pyrebase4.**

### Create Service Account

1. Project Settings → **Service Accounts** tab
2. Click **Generate new private key**
3. Save as `service-account.json` in `rpi/` directory
4. **Add to `.gitignore`!**

### Use with firebase-admin

```python
# rpi/firebase_admin_setup.py
import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate('service-account.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://your-project-default-rtdb.asia-southeast1.firebasedatabase.app'
})

# Now use admin SDK
ref = db.reference('/readings/wm_001')
```

### Why Pyrebase4 Instead?

| Feature | Pyrebase4 | firebase-admin |
|---------|-----------|----------------|
| Email/Password Auth | ✅ Native | ❌ Requires custom token |
| Client-side SDK style | ✅ | ❌ Server-only |
| ESP32 compatibility | Same auth method | Different auth |
| **Recommendation** | **Use Pyrebase4** | Only for admin tasks |

---

## Firebase Console Tour

### Key Pages to Bookmark

| Page | URL Path | Purpose |
|------|----------|---------|
| **Project Overview** | `/project/<project-id>/overview` | Dashboard, usage, links |
| **Realtime Database** | `/project/<project-id>/database` | View data, rules, backups |
| **Authentication** | `/project/<project-id>/authentication` | Users, providers, settings |
| **Project Settings** | `/project/<project-id>/settings/general` | Config, API keys, service accounts |
| **Usage & Billing** | `/project/<project-id>/usage` | Monitor free tier usage |

### Realtime Database Tab

- **Data:** View/edit JSON tree in real-time
- **Rules:** Security rules editor + playground
- **Backups:** Manual/automated backups (Blaze plan)
- **Usage:** Connections, bandwidth, storage

### Authentication Tab

- **Users:** List all users, disable/enable, reset password
- **Sign-in Method:** Enable/disable providers
- **Settings:** Authorized domains, templates, advanced

---

## Pricing & Limits

### Spark Plan (Free) — Sufficient for Development

| Resource | Limit | Notes |
|----------|-------|-------|
| **Realtime DB Storage** | 1 GB | ~200 MB for 30 days of readings |
| **Simultaneous Connections** | 100 | ESP32 (1) + RPi (1) + Dashboard (few) |
| **Bandwidth/Month** | 10 GB | ~2 GB/month for 1 device @ 5s interval |
| **Authentication** | Unlimited | Email/password users |
| **Hosting** | 10 GB | Not used in this project |

### Estimated Usage (1 Device, 5s Interval)

| Metric | Daily | Monthly |
|--------|-------|---------|
| **Writes** | 17,280 | 518,400 |
| **Reads (RPi poll)** | 17,280 | 518,400 |
| **Storage (90 days)** | ~200 MB | ~200 MB |
| **Bandwidth** | ~60 MB | ~1.8 GB |

### Free Tier Headroom

- Spark plan: **50K reads/day, 20K writes/day**
- Our usage: **~17K reads + 17K writes = 34K ops/day** ✅
- **Comfortable for 1-3 devices** on free tier

### Blaze Plan (Pay-as-you-go) — When Needed

- > 3 devices, or
- > 1 GB storage, or
- Need automated backups
- Cost: ~$0.18/GB storage, $1/GB bandwidth, $0.01/100K ops

---

## Troubleshooting

### Issue: "Permission denied" on Database Rules

**Cause:** Rules don't match auth UID
**Fix:** 
1. Check UID in Authentication → Users
2. Update rules with correct UIDs
3. Test in Rules Playground

### Issue: "Auth token expired" in RPi logs

**Cause:** ID token expires (1 hour)
**Fix:** Pyrebase4 should auto-refresh. Verify:
```python
# In firebase_listener.py _refresh_token()
try:
    self.user = self.auth.refresh(self.user['refreshToken'])
    self.id_token = self.user['idToken']
except:
    # Full re-auth
    self.user = self.auth.sign_in_with_email_and_password(EMAIL, PASSWORD)
    self.id_token = self.user['idToken']
```

### Issue: ESP32 "Firebase not ready" / "Token generation failed"

**Cause:** Wrong API key, email, or password
**Fix:**
1. Verify `FIREBASE_API_KEY` = Web API Key (Project Settings → General)
2. Verify email/password match Authentication → Users exactly
3. Ensure Email/Password provider is enabled

### Issue: "Database URL not set"

**Cause:** Missing or wrong `FIREBASE_DATABASE_URL`
**Fix:** Copy from Realtime Database → Data tab (top of page)
Format: `https://<project-id>-default-rtdb.<region>.firebasedatabase.app`

### Issue: RPi "Invalid API key" / "400 Bad Request"

**Cause:** Using wrong config values
**Fix:** Ensure `firebase_config.json` matches Web App config exactly:
- `apiKey` = Web API Key
- `databaseURL` = Realtime DB URL
- `authDomain` = `<project-id>.firebaseapp.com`

### Issue: Data not appearing in Firebase Console

**Check:**
1. ESP32 Serial: "Data uploaded to Firebase"?
2. ESP32 Serial: WiFi connected? Firebase ready?
3. Firebase Console → Data tab → Refresh
4. Rules allow write for ESP32 UID?

---

## Quick Config Reference

### ESP32 (config.h)

```cpp
#define FIREBASE_API_KEY       "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
#define FIREBASE_DATABASE_URL  "https://your-project-default-rtdb.asia-southeast1.firebasedatabase.app"
#define FIREBASE_USER_EMAIL    "esp32@your-project.iam.gserviceaccount.com"
#define FIREBASE_USER_PASSWORD "YourStrongPassword123!"
#define DEVICE_ID              "wm_001"
```

### RPi (.env)

```bash
FIREBASE_EMAIL=esp32@your-project.iam.gserviceaccount.com
FIREBASE_PASSWORD=YourStrongPassword123!
DEVICE_ID=wm_001
```

### RPi (firebase_config.json)

```json
{
  "apiKey": "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "authDomain": "your-project.firebaseapp.com",
  "databaseURL": "https://your-project-default-rtdb.asia-southeast1.firebasedatabase.app",
  "projectId": "your-project",
  "storageBucket": "your-project.appspot.com",
  "messagingSenderId": "123456789012",
  "appId": "1:123456789012:web:abcdef1234567890"
}
```

---

## Official References

- [Firebase Realtime Database Docs](https://firebase.google.com/docs/database)
- [Firebase Authentication Docs](https://firebase.google.com/docs/auth)
- [Firebase Security Rules](https://firebase.google.com/docs/database/security)
- [Firebase Pricing](https://firebase.google.com/pricing)
- [Pyrebase4 GitHub](https://github.com/nhorvath/Pyrebase4)
- [Firebase-ESP-Client GitHub](https://github.com/mobizt/Firebase-ESP-Client)

---

## Next Steps

Proceed to:
1. [Project Setup Guide](./setup.md) — Complete system deployment
2. [ESP32 Setup Guide](./esp32-setup-guide.md) — Firmware upload
3. [RPi Backend Guide](./rpi-backend.md) — Backend deployment

---

*Last updated: July 2026 | Firebase Console UI v2026 | Tested with Spark (Free) Plan | Compatible with ESP32 NodeMCU-32S, RPi 4/5*