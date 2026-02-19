"""Quick Start Guide for Change Management Analysis System"""

# 🚀 QUICK START GUIDE

Follow these steps to get the system up and running in 5 minutes.

## Step 1: Get Your Groq API Key (2 minutes)

1. Go to https://console.groq.com/keys
2. Create a free account if you don't have one
3. Click "Create API Key"
4. Copy the key to your clipboard

## Step 2: Configure Environment (1 minute)

In Windows PowerShell:

```powershell
cd C:\Users\Govind\Projects\IncidenceManagment
cp .env.example .env
```

Edit `.env` file with your API key:
```
GROQ_API_KEY=your_copied_key_here
```


## Step 3: Install Dependencies (1 minute)

Using uv (recommended):
```powershell
uv sync
```

Or using pip:
```powershell
pip install -r requirements.txt
```

## Step 4: Generate Sample Data (optional, <1 minute)

```powershell
python sample_data/generate_samples.py
```

This creates test data: `sample_data/sample_changes.xlsx`

## Step 5: Run The Application (1 minute)

```powershell
streamlit run app.py
```

The app opens at: http://localhost:8501

## 🎯 First Test

1. Go to "📋 Single Analysis" page
2. Fill in a change request (or use template values from README)
3. Click "Analyze Change Request"
4. Watch the AI analyze in real-time!

## 📊 Test Bulk Analysis

1. Go to "📁 Bulk Analysis" page
2. Click "Upload Excel file"
3. Select `sample_data/sample_changes.xlsx`
4. Click "Start Analysis"
5. Watch 25 changes process automatically!

## 📈 View Results

- Go to "📊 Analytics" to see overall statistics
- Go to "🔍 History" to search past analyses
- All results are saved to SQLite database

## 🎓 Next Steps

1. **Customize Prompts**: Edit `config/prompts.py` to adjust analysis style
2. **Adjust Thresholds**: Edit `.env` to change risk score thresholds
3. **Add Policies**: Add more policy docs to `policies/` folder
4. **Integrate Data**: Connect to your systems via API/webhooks
5. **Deploy**: Deploy to cloud (Heroku, AWS, Azure, etc.)

## ⚙️ Configuration Options

Key settings in `.env`:

```
# Model selection
LLM_MODEL=llama-3.1-70b-versatile  # Best accuracy
# OR
LLM_MODEL=llama-3.1-8b-instant     # Faster, cheaper

# Risk thresholds
RISK_APPROVE_THRESHOLD=25
RISK_REJECT_THRESHOLD=75

# Database
DATABASE_PATH=./data/changes.db

# Bulk processing
BULK_PROCESSING_DELAY_SECONDS=1
```

## 🐛 Common Issues

**"GROQ_API_KEY not set"**
- Check .env file exists and has your key

**"Failed to initialize engines"**
- Verify internet connection
- Confirm Groq API key is valid
- Check rate limits

**"Port 8501 already in use"**
```powershell
streamlit run app.py --server.port 8502
```

## 📞 Getting Help

1. Check logs: `logs/app.log`
2. Read full README.md for detailed documentation
3. Review policy documents in `policies/` folder
4. Check Streamlit documentation: https://docs.streamlit.io

## ✅ Success Checklist

- [ ] `.env` file configured with API key
- [ ] Dependencies installed (uv sync or pip install)
- [ ] Sample data generated (optional)
- [ ] Streamlit app starts without errors
- [ ] Can navigate all 5 pages
- [ ] Single analysis completes successfully
- [ ] Results save to database
- [ ] Analytics dashboard shows data

## 🎉 You're Ready!

The system is now running and ready to analyze production changes!

### Time to First Analysis: ~5 minutes
### Time to Bulk Analyze 25 Changes: ~2-3 minutes
### Decision Quality: Professional grade with reasoning

---

For production deployment, see the main README.md for additional configuration and best practices.
