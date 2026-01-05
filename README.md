# GrizzlyScripts

A collection of automation scripts for managing student accounts, rostering, and inventory systems. These scripts are tailored to our organization's specific workflows and integrations.

**Note:** This repository is public but many scripts are organization-specific and may require adaptation for use elsewhere.

## Overview

This repository contains Python scripts that automate various administrative tasks across two main areas:

### Accounts and Rostering (`accounts_and_rostering/`)

Scripts for managing student and staff accounts across multiple systems including FileMaker, Google Workspace, Active Directory, and third-party platforms.

**Key Scripts:**

- **`single_student.py`** - Orchestrates the complete student onboarding workflow
- **`new-staff/`** - New staff member account creation
- **`drop_student/`** - Student removal workflow
- **`google_group_update/`** - Google Groups membership management
- **`google_classroom_label/`** - Automated Gmail label creation for Google Classroom
- **`uploadprofilepic/`** - Profile picture management and upload to Google
- **`facecrop/`** - Automated face cropping for profile photos
- **`active_directory/`** - Active Directory student account cleanup
- **`aeries/`** - Aeries SIS student accoutn email notifications
- **`clevergenFMAPI/`** - Clever rostering file generation from FileMaker
- **`tabeonline/`** - TABE Online (DRC Insight) student data export
- **`filemaker_api/`** - Shared FileMaker Data API integration module

### Inventory Management (`inventory/`)

Scripts for managing Chromebook and device inventory using Snipe-IT.

**Key Scripts:**

- **`chromebook_repair/chromebook_maintenance.py`** - Automated Chromebook maintenance workflow (damage reporting, check-in, status updates)
- **`inventory_barcodescan.py`** - Barcode scanning for inventory management

## Prerequisites

### General Requirements

- Python 3.6 or higher
- Virtual environment (recommended)

### System-Specific Requirements

Different scripts require access to various systems:

- **FileMaker Server** - Student information database
- **Google Workspace** - User and group management
- **Active Directory** - Windows domain accounts
- **Snipe-IT** - Asset inventory management
- **Aeries SIS** - Student information system
- **Clever** - Rostering platform
- **TABE Online/DRC Insight** - Testing platform

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/GrizzlyScripts.git
cd GrizzlyScripts
```

2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Most scripts use environment variables for configuration. Create a `.env` file in the appropriate script directory with required credentials and settings.

### Common Environment Variables

**FileMaker Configuration:**

```
FMS_URL=https://your-filemaker-server.com
FMS_USERNAME=api_user
FMS_PASSWORD=api_password
FMS_DATABASE=YourDatabase
FMS_LAYOUT=LAYOUT
FMS_LIMIT=500
```

**Google Workspace:**

- Requires GAM (Google Apps Manager) or similar tooling
- Service account credentials for API access

**Snipe-IT Configuration:**

```
SNIPEIT_API_KEY=your-api-key
SNIPEIT_BASE_URL=https://your-instance.snipe-it.io/api/v1
SNIPEIT_DAMAGED_STATUS_ID=3
SNIPEIT_SUPPLIER_ID=1
```

**Organization-Specific:**

```
DISTRICT_CODE=your-district-code
SCHOOL_CODE=your-school-code
CLASS_NUMBER=your-class-number
OUTPUT_FOLDER=/path/to/output
```

Refer to individual script documentation (`CLAUDE.md`, `README.md`, `SETUP.md` files in subdirectories) for specific configuration requirements.

## Usage

Scripts are designed to be run individually as needed. Many include interactive prompts or CLI menus.

### Example: Student Onboarding Workflow

```bash
cd accounts_and_rostering
python3 single_student.py
```

### Example: Chromebook Maintenance

```bash
cd inventory/chromebook_repair
python3 chromebook_maintenance.py
```

### Example: TABE Export

```bash
cd accounts_and_rostering/tabeonline
python3 tabe_export.py
```

## Documentation

Individual scripts and modules may include additional documentation:

- `CLAUDE.md` - AI assistant guidance and detailed architecture
- `README.md` - Script-specific documentation
- `SETUP.md` - Setup and configuration instructions

## Security Notes

- Never commit credentials or API keys to version control
- Use environment variables or `.env` files (already in `.gitignore`)
- Restrict API permissions to minimum required access
- Review scripts before running in production environments

## Organization-Specific Workflows

Many scripts implement workflows specific to our organization's procedures:

- Platoon-based grouping and prefixes
- FileMaker as the source of truth for student data
- Integration with Google Apps Directory Sync
- Chromebook assignment and tracking
- Multi-step onboarding processes with manual approval gates

These workflows may need significant adaptation for use in other environments.

## Contributing

This repository is maintained for internal use. If adapting scripts for your organization, please fork the repository and modify as needed.

## Support

For questions or issues specific to these scripts, please open an issue in this repository.
