# Contractors in Email Attachments

A Flask-based REST API service that processes emails, extracts contractor information (primarily Russian tax identification numbers - INNs) from email bodies and attachments, and returns the data in a structured JSON format.

## Overview

This service connects to an email server via IMAP, retrieves emails by their message ID, and extracts contractor information from both the email body and any attachments. It can process various attachment types including PDF, CSV, and DOCX files. The extracted information is returned as a JSON response through a RESTful API endpoint.

## Features

- Email retrieval via IMAP
- Attachment processing (PDF, CSV, DOCX)
- Extraction of contractor INN (Russian tax identification numbers)
- RESTful API endpoint
- Health monitoring system
- Email alerts for system failures
- Docker deployment support
- Garbage collection optimization
- Logging and error handling

## Architecture

The application consists of several key components:

1. **Flask API Server** (`app.py`): Provides the REST API endpoint for processing emails
2. **Email Client** (`src/modules/email/client.py`): Handles IMAP connection and email retrieval
3. **Message Processor** (`src/modules/parsers/message.py`): Orchestrates the parsing process
4. **Attachment Parser** (`src/modules/parsers/attachment.py`): Extracts and processes email attachments
5. **Text Parser** (`src/modules/parsers/text.py`): Parses text to extract contractor information
6. **Health Checker** (`health_check.py`): Monitors the API service and sends alerts if it's down

## Requirements

- Python 3.x
- IMAP-enabled email account
- Dependencies: see `build/requirements.txt`

## Installation

### Local Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd contractors-in-email-attach
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install system dependencies for document processing:
   ```bash
   sudo apt install -y default-jre libleptonica-dev libreoffice-java-common libreoffice-writer \
       libtesseract-dev poppler-utils python3-pil tesseract-ocr tesseract-ocr-eng tesseract-ocr-rus \
       tesseract-ocr-script-latn unoconv
   ```

5. Create a `.env` file with your configuration (see Configuration section)

6. Run the application:
   ```bash
   python app.py
   ```

### Docker Installation

#### Using docker-compose (recommended)

1. Create a `.env` file with SERVER, EMAIL, PASS parameters
2. From the 'build' directory, run:
   ```bash
   sudo docker compose -f docker-compose.yaml up --build
   ```

#### Manual Docker Build

1. Build the Docker image:
   ```bash
   sudo docker build --force-rm -t api-contactor-parser -f ./build/Dockerfile .
   ```

2. Run the container:
   ```bash
   sudo docker run -p 8000:8000 -e EMAIL=$EMAIL -e PASS=$PASS -e SERVER=$SERVER api-contactor-parser:latest
   ```

## Configuration

### Main Application

Create a `.env` file in the project root with the following parameters:

```
SERVER=<imap-server-address>  # e.g., imap.gmail.com
EMAIL=<your-email>
PASS=<your-password>
```

### Health Checker

For the health checker, add these parameters to your `.env` file:

```
SERVER_URL=<api-server-url>  # e.g., http://localhost:8000
SMTP_SERVER=<smtp-server>  # e.g., smtp.gmail.com
SMTP_USERNAME=<email-for-alerts>
SMTP_PASSWORD=<email-password>
TO_EMAIL=<recipient-email>  # Can be comma-separated for multiple recipients
```

## Usage

### API Endpoints

#### GET /

Returns a simple status message to confirm the service is running.

**Example:**
```bash
curl http://localhost:8000/
```

**Response:**
```
This is contractor parser
```

#### GET /api/parsing/

Processes an email by its message ID and returns extracted contractor information.

**Parameters:**
- `mid`: The message ID of the email to process

**Example:**
```bash
curl http://localhost:8000/api/parsing?mid=02e901d9897e$a9e08ad0$fda1a070$@timer73.ru
```

**Response:**
```json
{
  "inns": ["1234567890", "0987654321"]
}
```

### Health Checker

The health checker continuously monitors the API service and sends email alerts if it becomes unresponsive.

To run the health checker:

```bash
python health_check.py
```

## Troubleshooting

### Common Issues

1. **IMAP Connection Errors**
   - Verify your email credentials in the `.env` file
   - Ensure IMAP is enabled for your email account
   - Check if your email provider requires app-specific passwords

2. **Attachment Processing Errors**
   - Ensure all system dependencies are installed
   - Check the logs for specific error messages

3. **Health Checker Alerts**
   - Verify the API service is running
   - Check network connectivity between the health checker and API service
