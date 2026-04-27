Fleet Logger API 🚛
A robust backend system designed to digitize and optimize logistics operations. This API facilitates trip documentation, fuel monitoring, and maintenance logging for fleet management.  

🚀 Tech Stack
Framework: Django & Django REST Framework (DRF)  

Database: PostgreSQL  

Containerization: Docker & Docker Compose  

Cloud Infrastructure: AWS (EC2/RDS) / OCI (Targeted)  

CI/CD: GitHub Actions  

Frontend Hosting: Vercel  

⚙️ Core Features  
Vehicle Management: Track vehicle specifications, maintenance schedules, and performance metrics.  

Trip Logging: Record route details, driver information, and timestamps for every journey.  

Fuel Monitoring: Automated tracking of fuel consumption and costs across the fleet.  

Secure API: Token-based authentication for mobile and web frontends.

Cloud Scalability: Decoupled architecture allowing the Django server and PostgreSQL database to scale independently.  

## Project Structure  

```text
.
├── fleet/               # Main API Application (Django)
├── users/               # User Authentication & Profiles
├── vehicle_fleet/       # Project Configuration & Settings
├── new_frontend/        # Vibe-coded JS Dashboard (Vercel Hosted)
├── nginx/               # Nginx Reverse Proxy Configs
├── docker-compose.yml   # Orchestration for Backend & DB
├── Dockerfile           # Backend Containerization
├── gunicorn_config.py   # Gunicorn config file
└── requirements.txt     # Python Dependencies

[!NOTE]
The new_frontend is a decoupled JavaScript application. While the backend runs on Docker/AWS, the frontend is optimized for CI/CD deployment via Vercel.
```
🚦 Getting Started (Local Development)  
Prerequisites  
Docker & Docker Compose  

Python 3.11+  

Installation  
Clone the repository:  

Bash
git clone https://github.com/mohanishParganiha/Fleet-Logger-App.git
cd Fleet-Logger-App
Set up environment variables:
Create a .env file in the root directory:

Code snippet
```bash
DEBUG=True
SECRET_KEY=your-secret-key-here-change-me
DB_NAME=fleet_db
DB_USER=fleet_user
DB_PASSWORD=your-secure-password
DB_HOST=your-rds-endpoint.amazonaws.com
DB_PORT=5432
ALLOWED_HOSTS=yourdomain.com,your-ec2-ip-address
CORS_ALLOWED_ORIGINS=http://localhost,http://127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost
```
Run with Docker Compose:
```bash
docker-compose up --build
```
🚢 Deployment  
The API is configured for a professional CI/CD pipeline using GitHub Actions.  

Testing: Automated test suite runs on every push using a PostgreSQL sidecar service.  

Build: Docker images are packaged and prepared for distribution.  

Deployment: Automated via SSH to cloud instances (AWS EC2 / OCI), ensuring zero-downtime migrations and static file collection.  
