# DBeaver Setup for EFF Database

## Quick Start

### 1. Start Cloud SQL Proxy

Open PowerShell and run:
```powershell
C:\Users\rurbi\Projects\EFF\google\scripts\start-cloud-sql-proxy.ps1
```

Or manually (cloud-sql-proxy v2 syntax):
```powershell
$proxy = "C:\Users\rurbi\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\cloud-sql-proxy.exe"
& $proxy sublime-scion-499902-m5:us-central1:eff-db --port 3306 --address 127.0.0.1
```

The proxy will start and listen on `localhost:3306`.

### 2. Configure DBeaver Connection

Create two connections — one for prod, one for dev. All settings are the same except the database name.

| Setting | Prod | Dev |
|---------|------|-----|
| **Server Host** | localhost | localhost |
| **Port** | 3306 | 3306 |
| **Database** | `eff_db` | `eff_db_dev` |
| **Username** | appuser | appuser |
| **Password** | W5JAo9NFIX0tXSaVEuZlSs8LVbcwa8en | W5JAo9NFIX0tXSaVEuZlSs8LVbcwa8en |

Both databases are on the same Cloud SQL instance — the proxy connection is shared.

1. Open DBeaver
2. **File → New → DBeaver → Database Connection**
3. Select **MySQL** → Next
4. Fill in the settings from the table above
5. Click **Test Connection** → Should see "Connected"
6. Click **Finish**
7. Repeat for the second connection

### 3. Verify Connection

You should now see the `eff_dev_db` database in DBeaver with all tables:
- `MatchDaysStatus`
- `Users`
- `Leagues`
- `Teams`
- etc.

## Common Tasks

### View MatchDaysStatus Records

```sql
SELECT 
    matchDayMapKey,
    realCompetitionMatchDay,
    scriptsStatus,
    startWaivers,
    finishPostMatch,
    startMatchDay,
    finishMatchDay
FROM MatchDaysStatus
WHERE matchDayMapKey = '21'
ORDER BY realCompetitionMatchDay;
```

### Check Current Match Day Status

```sql
SELECT 
    realCompetitionMatchDay,
    scriptsStatus,
    startWaivers,
    finishPostMatch,
    CURRENT_TIMESTAMP as now
FROM MatchDaysStatus
WHERE matchDayMapKey = '21'
AND CURRENT_TIMESTAMP >= startWaivers
AND CURRENT_TIMESTAMP < finishPostMatch;
```

### Populate Missing scriptsStatus Values

```sql
UPDATE MatchDaysStatus
SET scriptsStatus = 'PostMatch'
WHERE matchDayMapKey = '21'
AND scriptsStatus IS NULL;
```

## Troubleshooting

### Connection Refused
- Ensure Cloud SQL Proxy is running
- Check that you can see the proxy output: `Listening on 127.0.0.1:3306`

### Authentication Failed
- Verify username is `appuser`
- Check password is correct (from Secret Manager)
- Ensure database name is `eff_dev_db` (no underscore variations)

### Proxy Window Closes Immediately
- Run the PowerShell script with `-NoExit` flag:
  ```powershell
  powershell -NoExit C:\Users\rurbi\Projects\EFF\google\scripts\start-cloud-sql-proxy.ps1
  ```

### Check Firewall
- Cloud SQL Proxy should be allowed through Windows Firewall
- If blocked, whitelist it in Windows Security settings

## Cloud SQL Instance Details

- **Project**: sublime-scion-499902-m5 (EFFootball)
- **Region**: us-central1
- **Instance Name**: eff-db
- **MySQL Version**: 8.4

| Database | Used by |
|----------|---------|
| `eff_db` | Production — `https://eff-api-338220807664.us-central1.run.app` |
| `eff_db_dev` | Dev — `https://eff-api-dev-338220807664.us-central1.run.app` |

## Security Notes

- Cloud SQL Proxy uses IAM authentication (requires `gcloud auth login`)
- Credentials are stored in Secret Manager, not in the code
- Connection is encrypted through the proxy
- Don't share passwords in chat/commits
