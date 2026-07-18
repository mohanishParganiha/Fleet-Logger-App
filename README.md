Fleet Logger API 🚛
A robust backend system designed to digitize and optimize logistics operations. This API facilitates trip documentation, fuel monitoring, and maintenance logging for fleet management.
***
🚀 Tech Stack
Framework: Django & Django REST Framework (DRF)

Database: PostgreSQL (External/Managed)

Containerization: Docker & Docker Compose

Cloud Infrastructure: Oracle Cloud Infrastructure (OCI) / AWS

CI/CD: GitHub Actions

Frontend Hosting: Vercel
***
⚙️ Core Features
Vehicle Management: Track specifications, maintenance schedules, and performance.

Trip Logging: Record route details, driver info, and timestamps.

Fuel Monitoring: Automated tracking of consumption and costs.

Decoupled Architecture: Optimized for independent scaling of compute and data layers.

🔐 Authentication
The system uses a custom user model for enhanced security and flexibility:

Identifier: Authentication is performed via Email (the default Django username field has been deprecated in this project).

Methods: Fully supports both Token-based Authentication (for mobile/external clients) and Session Authentication (for web dashboard access).
***
🗺️ Project Structure
```bash
Plaintext
.
├── fleet/               # Main API Application (Django)
├── users/               # User Authentication & Profiles (Email-based)
├── config/       # Project Configuration & Settings
├── new_frontend/        # Decoupled JS Dashboard (Vercel)
├── nginx/               # Nginx Reverse Proxy Configs
├── docker-compose.yml   # Orchestration (App + Nginx)
├── Dockerfile           # Backend Containerization
└── requirements.txt     # Python Dependencies
```
>[!NOTE]
>The new_frontend is a decoupled application. While the backend runs on OCI/AWS, the frontend is optimized for CI/CD deployment via Vercel.
***
🚦 Getting Started (Local Development)
Prerequisites
Docker & Docker Compose

Python 3.11+

Installation
Clone the repository:

```bash
git clone https://github.com/mohanishParganiha/Fleet-Logger-App.git
cd Fleet-Logger-App
```
Configure Environment:
Create a .env file in the root directory. You must provide your own PostgreSQL instance details.

Run with Docker:

```Bash
docker-compose up --build
```
***
🚢 Deployment & Infrastructure
The API is deployed using a professional CI/CD pipeline via GitHub Actions.

>[!IMPORTANT]
>☁️ Cloud Infrastructure (OCI vs. AWS)
>
>This project is currently optimized for Oracle Cloud Infrastructure (OCI).

>[!WARNING]
>Database Constraints:
>
>Due to the resource limitations of smaller OCI "Always Free" instances, this setup does not support hosting the >PostgreSQL database within the same Docker environment or server.
>
>You must deploy or configure your own external PostgreSQL database.
>
>OCI: Use a separate VM or OCI Managed PostgreSQL.
>
>AWS: If hosting on AWS, use Amazon RDS.

>[!IMPORTANT]
>Configuration:
>
>If switching providers, ensure you update the .env variables and the GitHub Workflow YAML files to point to the correct DB host and credentials.

🔄 CI/CD Workflow
Testing: Automated suites run on every push using a PostgreSQL sidecar service.

Build: Docker images are packaged and prepared for distribution.

Deploy: Automated via SSH to OCI, ensuring zero-downtime migrations and automated static file collection.
