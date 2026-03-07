# Bradar - BGP Intelligence Platform

Global BGP Intelligence Platform for network monitoring and analysis.

## Features

- Global ASN database (85,000+ ASNs)
- Real-time BGP monitoring
- Country-based operator mapping
- Interactive global map
- Traffic analysis charts
- ASN search and details

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Nuxt 3 + Vue 3
- **Database**: SQLite
- **UI**: Nuxt UI + Tailwind CSS
- **Charts**: Chart.js
- **Maps**: Leaflet

## Quick Start

### Backend

```bash
cd mcp_brbgp
pip install -r requirements.txt
python main.py
```

API runs on http://localhost:8002

### Frontend

```bash
cd frontend-nuxt
npm install
npm run dev
```

Frontend runs on http://localhost:3000

## API Endpoints

- `/api/stats` - Global statistics
- `/api/search?q=` - Search ASNs
- `/api/asn/{id}` - ASN details
- `/api/operators` - List operators
- `/api/countries` - Country distribution
- `/api/traffic` - Traffic data
- `/api/global/operators` - Global operators with coordinates

## Database

The system uses SQLite with:
- 85,518 global ASNs
- 9,088 Brazilian ASNs
- IP range data
- Country information

## License

MIT
