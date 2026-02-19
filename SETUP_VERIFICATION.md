"""
SETUP VERIFICATION CHECKLIST
Complete this after installation to ensure everything works correctly
"""

# ✅ PRE-INSTALLATION CHECKLIST

## System Requirements
- [ ] Python 3.10+ installed: `python --version`
- [ ] uv installed: `uv --version`
- [ ] PowerShell or Command Prompt ready
- [ ] Stable internet connection
- [ ] ~500MB free disk space

## Groq API Setup
- [ ] Visit https://console.groq.com
- [ ] Account created (free tier available)
- [ ] API key generated
- [ ] API key copied to clipboard
- [ ] Key never needs credit card for free tier

---

# 🔧 INSTALLATION VERIFICATION

## Step 1: Environment Configuration
```
✅ REQUIRED:
- [ ] Project folder: C:\Users\Govind\Projects\IncidenceManagment
- [ ] .env file exists with GROQ_API_KEY filled in
- [ ] No spaces or special characters in API key value
```

**Verify with:**
```powershell
cat .env | grep GROQ_API_KEY
```
Should show your API key, not blank.

## Step 2: Dependencies Installation
```
✅ VERIFY Installation:
- [ ] All 14 packages installed: uv pip list | grep -E "streamlit|pydantic|langchain|chromadb"
- [ ] Specific versions match requirements.txt
- [ ] No error messages during installation
```

## Step 3: Database Initialization
```
✅ Database Setup:
- [ ] data/ folder exists
- [ ] data/changes.db will be created on first run (not needed before)
- [ ] logs/ folder exists
- [ ] policies/ folder exists with 3 .txt files
```

**Verify:**
```powershell
ls policies/
# Should show: change_management_policy.txt, security_policy.txt, deployment_standards.txt
```

## Step 4: Application Startup
```
✅ Successful Startup:
- [ ] No errors when running: streamlit run app.py
- [ ] Browser opens to http://localhost:8501
- [ ] Sidebar visible with navigation
- [ ] Home page shows "Change Management Analysis System" title
```

---

# 🧪 FUNCTIONALITY VERIFICATION

## Test 1: Single Analysis (5 minutes)
1. Click "📋 Single Analysis" in sidebar
2. Fill in form:
   - **Short**: "Update nginx worker count"
   - **Long**: "Updating worker process count to 8 to utilize 8-core CPU better"
   - **Type**: standard
   - **Category**: configuration
   - **Steps**: "1. SSH to server\n2. Edit config\n3. Restart nginx"
   - **Validation**: "1. Check processes\n2. Load test"
   - **Rollback**: "1. Restore config\n2. Restart"
   - **Window**: 2024-02-20T23:00:00Z
   - **Services**: "Web Server"
   - **Complexity**: low

3. Click "🔍 Analyze Change Request"
4. ✅ Should complete in ~5-10 seconds with decision banner
5. ✅ Should show green "APPROVE" decision
6. ✅ Risk score should be <25

## Test 2: Bulk Analysis (3 minutes)
1. Generate sample data: `python sample_data/generate_samples.py`
2. Click "📁 Bulk Analysis"
3. Upload `sample_data/sample_changes.xlsx`
4. Click "🚀 Start Analysis"
5. ✅ Should process 25 changes in 2-3 minutes
6. ✅ Results table shows mixed decisions (not all same)
7. ✅ Download CSV works

## Test 3: Analytics (1 minute)
1. After bulk analysis, click "📊 Analytics"
2. ✅ KPI cards show numbers (don't need to be large)
3. ✅ Charts render correctly
4. ✅ Download button works

## Test 4: History Search (2 minutes)
1. Click "🔍 History"
2. Click "🔍 Search" with default filters
3. ✅ Results table shows at least one analysis
4. ✅ Can click details and see full assessment

## Test 5: Database (1 minute)
1. Check database was created:
```powershell
ls data/
# Should show: changes.db, chroma_db (directory)
```

2. ✅ Both files/folders exist
3. ✅ Database is non-empty after analyses

---

# ⚠️ COMMON ISSUES & SOLUTIONS

| Issue | Solution |
|-------|----------|
| "GROQ_API_KEY not set" | Edit .env file, add key after = |
| Port 8501 already in use | `streamlit run app.py --server.port 8502` |
| Module not found errors | Run `uv sync` again to reinstall |
| Slow on first run | First LLM call initializes models (~30s ok) |
| Database locked | Close other instances, restart app |
| ChromaDB errors | Delete `data/chroma_db` folder, restart |
| API rate limit | Add delay: `BULK_PROCESSING_DELAY_SECONDS=2` in .env |

---

# 📊 SUCCESS INDICATORS

## Green Lights ✅
- [ ] Streamlit app starts without errors
- [ ] Single analysis completes <15 seconds
- [ ] Decision appears with color coding
- [ ] Bulk analysis processes 25 items without crashing
- [ ] Results table is populated with data
- [ ] Analytics shows numbers on cards
- [ ] History search returns results
- [ ] Database file is created and growing

## Yellow Warnings ⚠️
- First analysis slow (>20s) - This is normal, models initializing
- Some analyses show REVIEW_REQUIRED - This is expected for medium-risk changes
- Empty analytics on first run - Runs after you analyze some changes

## Red Errors ❌
- API key validation failures - Check your Groq API key
- Database locked errors - Close and restart app
- Module import errors - Run `uv sync` again
- Streamlit crashes - Check logs: `cat logs/app.log`

---

# 🎓 VERIFICATION COMMANDS

```powershell
# Check Python version
python --version
# Expected: Python 3.10+

# Check uv installation
uv --version
# Expected: uv 0.x.x (something positive)

# Check API key
type .env | findstr GROQ_API_KEY
# Expected: GROQ_API_KEY=gsk_... (actual key)

# Check dependencies
uv pip list | grep streamlit
# Expected: streamlit X.X.X

# Check project structure
ls -Recurse *.py | measure
# Expected: 20+ Python files

# Check logs after running
ls logs/
# Expected: app.log file exists
```

---

# 🚀 QUICK VERIFICATION SCRIPT

Save as `verify.ps1`:

```powershell
Write-Host "🔍 Verifying Change Management System Installation..." -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $version = python --version 2>$null
    Write-Host "✅ Python: $version" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found" -ForegroundColor Red
}

# Check uv
try {
    $uv = uv --version 2>$null
    Write-Host "✅ uv: $uv" -ForegroundColor Green
} catch {
    Write-Host "❌ uv not found" -ForegroundColor Red
}

# Check .env
if (Test-Path ".env") {
    Write-Host "✅ .env file exists" -ForegroundColor Green
    $key = Select-String "GROQ_API_KEY" .env
    if ($key -match "=.+") {
        Write-Host "✅ GROQ_API_KEY configured" -ForegroundColor Green
    } else {
        Write-Host "❌ GROQ_API_KEY is empty" -ForegroundColor Red
    }
} else {
    Write-Host "❌ .env file missing" -ForegroundColor Red
}

# Check folders
$folders = @("config", "core", "data", "utils", "pages", "policies")
foreach ($folder in $folders) {
    if (Test-Path $folder) {
        Write-Host "✅ Folder: $folder" -ForegroundColor Green
    } else {
        Write-Host "❌ Missing: $folder" -ForegroundColor Red
    }
}

# Check key files
$files = @("app.py", "requirements.txt", "README.md", "QUICKSTART.md")
foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "✅ File: $file" -ForegroundColor Green
    } else {
        Write-Host "❌ Missing: $file" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "✅ Verification complete!" -ForegroundColor Cyan
Write-Host "Ready to run: streamlit run app.py" -ForegroundColor Yellow
```

Run with: `powershell .\verify.ps1`

---

# 🎯 FINAL CHECKLIST BEFORE FIRST RUN

Before running `streamlit run app.py`, verify:

**System & Setup:**
- [ ] Python 3.10+ installed
- [ ] uv or pip working
- [ ] .env file with valid GROQ_API_KEY
- [ ] All folders exist (config, core, data, utils, pages, policies)

**Code & Configuration:**
- [ ] All Python files present in config/, core/, data/, utils/, pages/
- [ ] All policy documents in policies/
- [ ] requirements.txt has 14+ packages
- [ ] pyproject.toml properly formatted

**Dependencies:**
- [ ] Packages installed via `uv sync` or `pip install -r requirements.txt`
- [ ] No import errors: `python -c "import streamlit; import pydantic; import langchain"`
- [ ] ChromaDB installed: `python -c "import chromadb"`

**First Run:**
- [ ] Allow 30+ seconds for first analysis (model initialization)
- [ ] Check logs for errors: `cat logs/app.log`
- [ ] Verify database is created: `ls data/changes.db`
- [ ] Run simple test to ensure no crashes

---

**Once all items checked, you're ready to analyze changes!**

Run: `streamlit run app.py`

Then navigate to: http://localhost:8501

🎉 Success!
