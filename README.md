# 🔄 Change Management Analysis System

An AI-powered production change request analysis system using LLM and RAG for intelligent risk assessment and policy compliance checking.

## 📋 Overview

This system automatically analyzes production change requests and provides:

- **Intelligent Risk Assessment**: LLM-based analysis with 40-point scoring considering documentation quality, risk factors, and red flags
- **Policy Compliance Checking**: RAG-based verification against company policies using ChromaDB
- **Hybrid Risk Scoring**: Combines LLM assessment (40%) and rule-based scoring (60%)
- **Approval Recommendations**: Final decision (APPROVE / REVIEW_REQUIRED / REJECT) with detailed reasoning
- **Actionable Insights**: Specific, implementable recommendations for improvement

## 🎯 Key Features

✅ **Single Change Analysis**: Analyze one change request with detailed assessment  
✅ **Bulk Processing**: Upload Excel with multiple changes for batch analysis  
✅ **Analytics Dashboard**: KPIs, trends, and statistics visualization  
✅ **History & Search**: Query past analyses with filters  
✅ **SQLite Database**: Persistent storage with easy PostgreSQL migration  
✅ **RAG Compliance**: Policy checking with ChromaDB vector store  
✅ **Production Ready**: Full logging, error handling, type safety  

## 🛠️ Technology Stack

- **Frontend/Backend**: Streamlit (single framework)
- **Language**: Python 3.10+
- **LLM**: Groq API with LLaMA 3.1 (70B or 8B)
- **LLM Orchestration**: LangChain + langchain-groq
- **RAG Components**: ChromaDB + sentence-transformers embeddings
- **Database**: SQLite (designed for PostgreSQL migration)
- **Data Processing**: pandas, openpyxl
- **Validation**: Pydantic v2
- **Visualization**: Plotly
- **Configuration**: python-dotenv
- **Logging**: Python stdlib logging

## 📦 Project Structure

```
IncidenceManagement/
├── config/                          # Configuration management
│   ├── settings.py                 # Settings and environment config
│   └── prompts.py                  # LLM prompts (externalized)
│
├── core/                            # Core business logic
│   ├── models.py                   # Pydantic data models
│   ├── llm_engine.py               # Groq/LangChain integration
│   ├── rag_engine.py               # ChromaDB RAG system
│   ├── risk_scorer.py              # Hybrid risk calculation
│   └── decision_engine.py          # Final decision logic
│
├── data/                            # Data layer
│   ├── database.py                 # SQLAlchemy ORM models
│   └── repository.py               # Data access (DAO pattern)
│
├── utils/                           # Utilities
│   ├── logger.py                   # Logging configuration
│   ├── validators.py               # Input validation
│   └── excel_handler.py            # Excel parsing
│
├── pages/                           # Streamlit pages
│   ├── 01_Single_Analysis.py       # Single change analysis
│   ├── 02_Bulk_Analysis.py         # Bulk Excel processing
│   ├── 03_Analytics.py             # Dashboard and statistics
│   └── 04_History.py               # Search and history
│
├── policies/                        # Policy documents
│   ├── change_management_policy.txt
│   ├── security_policy.txt
│   └── deployment_standards.txt
│
├── sample_data/                     # Sample data and generation
│   └── generate_samples.py
│
├── app.py                           # Main Streamlit home page
├── requirements.txt                 # Dependencies
├── pyproject.toml                   # uv project configuration
├── .env.example                     # Environment variable template
├── .gitignore                       # Git ignore rules
└── README.md                        # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Groq API key (free tier available at https://console.groq.com)
- uv package manager

### Installation

1. **Clone/Set Up Project**:
```bash
cd IncidenceManagement
```

2. **Install Dependencies Using uv**:
```bash
uv sync
# Or install requirements directly
uv pip install -r requirements.txt
```

3. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with your Groq API key
nano .env
```

Required environment variables:
```
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=llama-3.1-70b-versatile  # or llama-3.1-8b-instant for faster/cheaper
```

4. **Generate Sample Data** (optional):
```bash
python sample_data/generate_samples.py
```

This creates `sample_data/sample_changes.xlsx` with 25 diverse test cases.

5. **Run Application**:
```bash
streamlit run app.py
```

The application will start at `http://localhost:8501`

## 📖 Usage Guide

### Single Analysis Page

1. Fill in all change request fields:
   - **Short Description**: 10-200 character summary
   - **Long Description**: Detailed explanation (min 20 chars)
   - **Change Type**: standard / normal / emergency
   - **Change Category**: configuration / infrastructure / deployment / database
   - **Implementation Steps**: Numbered step-by-step instructions
   - **Validation Steps**: How to verify success
   - **Rollback Plan**: Detailed rollback procedure
   - **Planned Window**: ISO datetime (e.g., 2024-02-20T22:00:00Z)
   - **Impacted Services**: Comma-separated list
   - **Complexity**: low / medium / high

2. Click "Analyze Change Request"

3. Review results:
   - **Decision Banner**: Color-coded APPROVE/REVIEW_REQUIRED/REJECT
   - **Metrics**: Risk score, confidence, compliance status
   - **Risk Factors**: Specific risks identified
   - **Compliance**: Policy violations (if any)
   - **Recommendations**: Actionable improvements
   - **Validation Suggestions**: Additional tests to run

4. Save analysis to database for future reference

### Bulk Analysis Page

1. Prepare Excel file with columns:
   - Short Description
   - Long Description
   - Change Type
   - Change Category
   - Implementation Steps
   - Validation Steps
   - Rollback Plan
   - Planned Window
   - Impacted Services
   - Complexity

2. Upload `.xlsx` or `.xls` file

3. Click "Start Analysis"

4. Monitor progress with real-time updates

5. Download results as CSV or Excel

### Analytics Dashboard

- View KPIs: Total analyzed, approval rate, average risk, confidence
- Visualizations: Decision breakdown, risk distribution, category breakdown
- Filters: Date range, adjust historical analysis window
- Export analytics data as CSV

### History & Search

- **Full-text search**: Search in change descriptions
- **Filters**: By decision type, risk range, date range
- **View details**: Click analysis to see complete assessment
- **Export**: Download search results as CSV

## 🔧 Configuration

### Thresholds
   
Adjust in `.env`:
```
RISK_APPROVE_THRESHOLD=25       # Risk score <25 → auto-approve
RISK_REJECT_THRESHOLD=75        # Risk score >75 → flag for review/rejection
```

### LLM Model Selection

```
# For accuracy (slower/more expensive):
LLM_MODEL=llama-3.1-70b-versatile

# For speed/cost (faster/cheaper):
LLM_MODEL=llama-3.1-8b-instant
```

### Database

Default: SQLite at `./data/changes.db`

To use PostgreSQL later:
1. Update `data/database.py` connection string
2. Migrations handled automatically by SQLAlchemy

### RAG Embeddings

```
EMBEDDINGS_MODEL=all-MiniLM-L6-v2  # Recommended
CHUNK_SIZE=1000                     # Document chunk size
CHUNK_OVERLAP=200                   # Chunk overlap for context
```

## 📊 Decision Logic

The system makes decisions based on:

1. **Compliance Violations** (highest priority)
   - Critical violations → REVIEW_REQUIRED
   - Warning violations → Considered but not blocking

2. **Risk Score** (primary signal)
   - Score < 25 → APPROVE (if compliant)
   - Score 25-75 → REVIEW_REQUIRED (needs expert input)
   - Score > 75 → REJECT (unless compliant as override)

3. **LLM Recommendation** (tiebreaker for medium risk)
   - Used when risk score is in review threshold
   - Confidence considered

4. **Compliance Status** (safety override)
   - Non-compliant changes cannot be auto-approved
   - Flag for review if compliance issues exist

## 🧠 Risk Scoring Details

### LLM Risk Score (40% weight)

Factors considered:
- Documentation quality and completeness
- Service criticality
- Blast radius
- Reversibility
- Testing comprehensiveness
- Timing appropriateness

### Rule-Based Risk Score (60% weight)

Breakdown:
- Complexity: (10-60 points)
- Category: (10-40 points)
- Impact scope: (10-70 points)
- Documentation penalties: (0-20 points)
- Timing penalties: (0-30 points)
- Rollback completeness: (0-20 points)
- Validation completeness: (0-20 points)

**Final Score** = (LLM × 0.4) + (RuleBased × 0.6)

## 📚 Documentation

### Change Request Format

**Required Fields**:

| Field | Length | Format | Notes |
|-------|--------|--------|-------|
| short_description | 10-200 | Text | Clear, specific |
| long_description | 20+ | Text | Detailed explanation |
| change_type | - | Enum | standard/normal/emergency |
| change_category | - | Enum | category/infrastructure/etc |
| implementation_steps | 10+ | Text | Numbered steps |
| validation_steps | 10+ | Text | How to verify |
| rollback_plan | 10+ | Text | Revert procedure |
| planned_window | - | ISO 8601 | 2024-02-20T22:00:00Z |
| impacted_services | - | CSV | Service1, Service2 |
| complexity | - | Enum | low/medium/high |

### Policy Documents

Three comprehensive policy documents are included:

1. **change_management_policy.txt**
   - Classification rules
   - Documentation requirements
   - Risk criteria
   - Testing/validation standards
   - Change windows
   - Prohibited actions

2. **security_policy.txt**
   - Authentication/authorization changes
   - Data handling rules
   - API security standards
   - Infrastructure security
   - Compliance requirements

3. **deployment_standards.txt**
   - Deployment strategies (blue-green, canary, rolling)
   - Monitoring requirements
   - Communication protocols
   - Database deployment rules
   - Rollback procedures

These are loaded into ChromaDB for RAG-based compliance checking.

## 🐛 Troubleshooting

### "GROQ_API_KEY is not set"
- Ensure `.env` file exists and contains your Groq API key
- Run `cp .env.example .env` and edit the file

### "Failed to initialize LLM Engine"
- Verify Groq API key is valid
- Check internet connection
- Confirm rate limits not exceeded

### "ChromaDB collection not found"
- Ensure policy documents exist in `policies/` folder
- ChromaDB automatically initializes on first run
- Check logs for initialization errors

### "Database locked"
- SQLite can have concurrency issues
- Consider PostgreSQL for production
- Check if other processes are accessing the database

### "Out of memory during bulk processing"
- Reduce batch size by adjusting `BULK_PROCESSING_DELAY_SECONDS`
- Process in smaller chunks
- Consider PostgreSQL with better resource management

## 📊 Example Analyses

### Low-Risk Approval

```
Change: Update nginx worker count configuration
Risk Score: 18/100 (LOW)
Decision: ✅ APPROVE

Why:
- Simple configuration change, low blast radius
- Non-critical service, easy rollback
- Off-hours timing reduces risk
```

### Medium-Risk Review

```
Change: Deploy API v2.1.0 with new endpoints
Risk Score: 48/100 (MEDIUM)
Decision: ⚠️ REVIEW_REQUIRED

Why:
- Needs expert review (user-impacting feature)
- Comprehensive staging testing completed
- Could benefit from additional load testing
```

### High-Risk Rejection

```
Change: Database migration without tested rollback
Risk Score: 82/100 (HIGH)
Decision: ❌ REJECT

Why:
- Missing tested rollback procedure (violation)
- High criticality database changes
- Insufficient documentation
- Needs comprehensive rollback testing first
```

## 🔒 Security

- **API Keys**: Never stored in code, use `.env`
- **Secrets**: Marked as not logged in logger
- **Database**: SQLite by default, use PostgreSQL with auth for production
- **Input Validation**: Pydantic models validate all inputs
- **SQL Safety**: SQLAlchemy parameterized queries prevent injection
- **Error Handling**: User-friendly messages, no stack traces exposed

## 📈 Performance

- **Single Analysis**: ~5-10 seconds
- **Bulk Analysis (25 changes)**: ~2-3 minutes
- **Database Queries**: <100ms
- **Embeddings**: Cached in ChromaDB, reused across sessions

## 🔄 Future Enhancements

Designed to support (not implemented):
- ServiceNow API integration
- Slack/email notifications
- PostgreSQL backend migration
- User authentication
- Multi-tenancy
- A/B testing of prompts
- Model fine-tuning on historical data
- Automated incident response triggering
- CI/CD pipeline integration

## 📝 Logging

Logs are written to:
- **Console**: INFO level and above
- **File**: `logs/app.log` (rotated at 10MB, keeps 5 backups)

Log format: `[YYYY-MM-DD HH:MM:SS] LEVEL - MODULE - FUNCTION:LINE - MESSAGE`

All operations are logged including:
- LLM analysis attempts and results
- Policy compliance checks
- Database operations
- API calls and failures
- Errors and exceptions

## 🧪 Testing

### Manual Testing Checklist

**Single Analysis**:
- [ ] Approve low-risk configuration change
- [ ] REVIEW_REQUIRED for medium-risk deployment
- [ ] Red flags detected for missing rollback
- [ ] Policy violations flagged appropriately

**Bulk Analysis**:
- [ ] All 25 sample changes process without errors
- [ ] Results vary (not all same decision)
- [ ] Progress bar shows real-time updates
- [ ] Export to CSV/Excel works

**Database**:
- [ ] Analyses save to SQLite
- [ ] Can retrieve analyses by ID
- [ ] Search/filters return correct data
- [ ] Analytics aggregations accurate

**UI/UX**:
- [ ] Navigation works across pages
- [ ] Charts render properly
- [ ] Color coding correct (green/yellow/red)
- [ ] Responsive on different screen sizes

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

This is a demonstration POC. For production use:
1. Add unit test suite
2. Implement authentication
3. Add API rate limiting
4. Consider distributed task queue for bulk processing
5. Migrate to PostgreSQL for concurrency
6. Add monitoring and alerting

## 📞 Support

For issues:
1. Check logs: `logs/app.log`
2. Review troubleshooting section above
3. Verify `.env` configuration
4. Check Groq API status

## 🎓 Learning Resources

- [Streamlit Docs](https://docs.streamlit.io)
- [LangChain Documentation](https://python.langchain.com)
- [ChromaDB Guide](https://docs.trychroma.com)
- [Groq API Docs](https://console.groq.com/docs)
- [Pydantic v2](https://docs.pydantic.dev/latest/)

---

**Built with ❤️ for production-grade change management**
