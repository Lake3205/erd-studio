# ERD Studio

Interactive ERD designer with:

- **Frontend**: Vue.js (drag/drop ERD canvas)
- **Backend**: Flask API (SQL script generation)
- **Database stack**: MariaDB + phpMyAdmin via Docker Compose

## Quick start (Docker Compose)

```bash
docker compose up --build
```

Apps:

- Frontend: http://localhost:5173
- Flask API: http://localhost:5000/api/health
- phpMyAdmin: http://localhost:8080
  - server: `mariadb`
  - username: `root`
  - password: `root`

## Local development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## SQL generation API

`POST /api/generate-sql`

Example payload:

```json
{
  "tables": [
    {
      "id": "users",
      "name": "users",
      "columns": [
        {"name": "id", "type": "INT", "primaryKey": true, "nullable": false},
        {"name": "email", "type": "VARCHAR(255)", "nullable": false}
      ]
    }
  ],
  "relationships": []
}
```
