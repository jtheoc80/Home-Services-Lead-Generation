# Home Services Lead Generation Platform

LeadLedgerPro - A comprehensive platform for generating and managing leads from building permit data across Texas municipalities.

## 🚀 Quick Start

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Backend API
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### ETL Pipeline
```bash
cd permit_leads
pip install -r requirements.txt
python -m permit_leads --source city_of_houston --sample --days 7
```

## 🏗️ Architecture

This platform consists of several integrated components:

- **Frontend**: Next.js application with Supabase integration for lead management
- **Backend**: FastAPI service for ML scoring and lead feedback
- **ETL Pipeline**: Python-based permit scraping and data processing
- **Automated Workflows**: GitHub Actions for continuous data collection

## 📊 Data Sources

Currently supports permit data from:
- Harris County, TX
- City of Houston, TX
- Dallas County, TX
- Austin, TX

## 🔧 Manual Operations

### Nightly ETL Guardian Bot

For immediate data refresh or troubleshooting, you can manually trigger the automated ETL pipeline:

**Actions → Nightly ETL Guardian Bot → Run workflow**

For detailed instructions on manual triggers, reviewing changes, and rollback procedures, see [docs/nightly-etl-bot.md](docs/nightly-etl-bot.md).

## 📚 Documentation

- [Frontend Setup](frontend/README.md) - Next.js application setup and configuration
- [Backend API](backend/README.md) - ML scoring and feedback system
- [ETL Pipeline](permit_leads/README.md) - Permit scraping and processing
- [GitHub Actions Runbook](docs/github-actions-runbook.md) - Workflow setup and troubleshooting
- [Nightly ETL Guardian Bot](docs/nightly-etl-bot.md) - Manual trigger and rollback guide
- [Copilot Allowlist Request](COPILOT_ALLOWLIST_REQUEST.md) - Required URL patterns for GitHub Copilot coding agent

## 🛠️ Development

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL (or Supabase)

### Environment Setup
1. Copy environment files:
   ```bash
   cp frontend/.env.example frontend/.env.local
   cp backend/.env.example backend/.env
   ```

2. Configure Supabase credentials in environment files

3. Install dependencies:
   ```bash
   # Frontend
   cd frontend && npm install

   # Backend
   cd backend && pip install -r requirements.txt

   # ETL Pipeline
   cd permit_leads && pip install -r requirements.txt
   ```

### Testing
```bash
# Frontend tests
cd frontend && npm test

# Backend tests
cd backend && python -m pytest

# ETL tests
cd permit_leads && python -m pytest tests/
```

## 🚀 Deployment

- **Frontend**: Deployed on Vercel with automatic deployments from main branch
- **Backend**: Can be deployed on Railway, Heroku, or any Python hosting service
- **ETL Pipeline**: Runs automatically via GitHub Actions workflows

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 📈 Features

### Lead Management
- Automated lead generation from permit data
- ML-powered lead scoring
- Contractor feedback integration
- Export capabilities

### Data Processing
- Real-time permit scraping
- Data normalization and validation
- Duplicate detection and deduplication
- Multi-format output (CSV, SQLite, JSONL)

### Automation
- Scheduled data collection
- Automated lead processing
- Continuous integration and testing
- Monitoring and alerting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- Check the [GitHub Actions Runbook](docs/github-actions-runbook.md) for workflow troubleshooting
- Review [docs/](docs/) for comprehensive documentation
- Open an issue for bugs or feature requests
