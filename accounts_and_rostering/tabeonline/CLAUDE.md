# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository is part of the GrizzlyScripts/accounts_and_rostering system for managing student data exports to TABE Online (DRC Insight). It exports student records from FileMaker Server to CSV format for import into the TABE testing platform.

## Architecture

### Core Components

**tabe_export.py** - Main export script with two export functions:
- `export_1112()`: Generates TABE_students_1112.csv for TABE Form 11/12
- `export_1314()`: Generates TABE_students_1314.csv for TABE Form 13/14
- Interactive CLI menu for selecting which export to generate

**filemaker_api module** (../filemaker_api/):
- Located in parent directory `accounts_and_rostering/filemaker_api/`
- Provides `filemaker_get_records()` function to retrieve student data from FileMaker Server
- Uses `fmrest` library to interact with FileMaker Data API
- Configuration via environment variables (see below)

### Data Flow

1. Script queries FileMaker Server for active students (`StatusActive: 'Yes'`)
2. Transforms FileMaker field names to DRC Insight format
3. Applies business logic (e.g., platoon prefixing, IEP status mapping)
4. Writes CSV to configured output folder

### Key Business Logic

- Student last names are prefixed with `{CLASS_NUMBER}{Platoon}` (e.g., "55A Smith")
- IEP status is mapped from "Yes"/"yes" to "Y", everything else to "N"
- Both export functions use identical headers but are separated to support different TABE form versions

## Environment Configuration

Required variables in `.env`:

```
DISTRICT_CODE       # DRC Insight district identifier
SCHOOL_CODE         # DRC Insight school identifier
OUTPUT_FOLDER       # Absolute path where CSV files are written
CLASS_NUMBER        # Prefix for student last names (e.g., 55)

# FileMaker Server configuration
FMS_URL            # FileMaker Server base URL
FMS_USERNAME       # API user credentials
FMS_PASSWORD       # API user credentials
FMS_DATABASE       # FileMaker database name
FMS_LAYOUT         # FileMaker layout name (typically "CADETAPI")
FMS_LIMIT          # Record retrieval limit (default: 500)
```

## Running the Script

```bash
# Run the interactive menu
python3 tabe_export.py
```

The script presents a menu:
1. Generate TABE FORM 11/12 export file
2. Generate TABE FORM 13/14 export file
3. Exit

## Dependencies

- Python 3.x
- `fmrest` - FileMaker Data API client
- `python-dotenv` - Environment variable management
- `rich` - Terminal UI (Console, Prompt)

## Related Scripts in Parent Repository

The parent directory (`accounts_and_rostering/`) contains a complete student onboarding pipeline:
- `filemaker_api/` - Shared FileMaker integration module
- `facecrop.py` - Photo processing
- `uploadprofilepic.py` - Google profile picture upload
- `google_group_update.py` - Google Groups management
- `google_classroom_label/` - Gmail label automation
- `active_directory/` - AD user creation
- `drop_student/` - Student removal workflow

## CSV Output Format

Headers for both TABE forms (11/12 and 13/14):
- District Code, School Code, Student ID
- Student Last Name (prefixed), Student First Name, Student Middle Initial
- Gender, Date of Birth
- Ethnicity and Race fields (American Indian/Alaskan Native, Asian, Black/African American, Native Hawaiian/Pacific Islander, Caucasian, Other)
- Public Assistance Status, IEP, 504, LEP/ELL
- Program, Additional Program, ESL Status, Labor Force Status
- HSE Certificate, HS Diploma
- Classified Accommodation fields (Reading, Mathematics, Language)
