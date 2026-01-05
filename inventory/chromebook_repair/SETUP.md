# Chromebook Maintenance Script Setup

## Prerequisites

- Python 3.6 or higher
- Access to your Snipe-IT instance
- API key with appropriate permissions

## Installation

1. Install required dependencies (if running outside of existing virtual environment):

```bash
pip install -r requirements.txt
```

## Configuration

The script requires the following environment variables:

### Required Variables

1. **SNIPEIT_API_KEY**: Your Snipe-IT API key

   - Generate from: Settings > API Keys in Snipe-IT

2. **SNIPEIT_BASE_URL**: Base URL of your Snipe-IT API

   - Format: `https://your-instance.snipe-it.io/api/v1`
   - Or: `https://your-domain.com/api/v1` (for self-hosted)

3. **SNIPEIT_DAMAGED_STATUS_ID**: The ID of your "Damaged" status
   - Find this in: Settings > Status Labels in Snipe-IT
   - Look at the URL when editing the status, or use the API

### Optional Variables

4. **SNIPEIT_SUPPLIER_ID**: (Optional) Default supplier ID for maintenance records

### Setting Environment Variables

#### Option 1: Export in terminal (temporary)

```bash
export SNIPEIT_API_KEY='your-api-key-here'
export SNIPEIT_BASE_URL='https://your-instance.snipe-it.io/api/v1'
export SNIPEIT_DAMAGED_STATUS_ID='3'
export SNIPEIT_SUPPLIER_ID='1'  # Optional
```

#### Option 2: Create a .env file (recommended)

Create a file named `.env` in the same directory:

```
SNIPEIT_API_KEY=your-api-key-here
SNIPEIT_BASE_URL=https://your-instance.snipe-it.io/api/v1
SNIPEIT_DAMAGED_STATUS_ID=3
SNIPEIT_SUPPLIER_ID=1
```

Then load it before running:

```bash
source .env  # or use python-dotenv
```

#### Option 3: Edit the script directly

Update the default values in `chromebook_maintenance.py`:

```python
BASE_URL = 'https://your-instance.snipe-it.io/api/v1'
API_KEY = 'your-api-key'
DAMAGED_STATUS_ID = 3
SUPPLIER_ID = 1
```

## Finding Your Status ID

To find your "Damaged" status ID, you can:

1. **Via Web Interface:**

   - Go to Settings > Status Labels
   - Click Edit on your "Damaged" status
   - Look at the URL: `.../statuslabels/3/edit` (3 is the ID)

2. **Via API:**
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        https://your-instance.snipe-it.io/api/v1/statuslabels
   ```

## Usage

Run the script:

```bash
python chromebook_maintenance.py
```

You'll be prompted to enter:

1. Asset tag (e.g., `CHR-12345`)
2. Maintenance reason (e.g., `Cracked screen`)

The script will then automatically:

1. Find the asset by tag
2. Create a maintenance record
3. Check in the asset if it's checked out
4. Update the status to "Damaged"

## Example Session

```
============================================================
Chromebook Maintenance Workflow
============================================================

Enter asset tag: CHR-12345
Enter maintenance reason (e.g., Cracked screen): Cracked screen

============================================================
Starting maintenance workflow...
============================================================

[1/4] Fetching asset with tag: CHR-12345
✓ Found asset: Chromebook Dell 3100 (ID: 456)
  Status: Checked out

[2/4] Creating maintenance record...
✓ Maintenance created successfully (ID: 789)

[3/4] Asset is checked out, checking in...
✓ Asset checked in successfully

[4/4] Updating asset status to 'Damaged'...
✓ Asset status updated to 'Damaged'

============================================================
Workflow completed successfully!
============================================================

Asset: Chromebook Dell 3100 (CHR-12345)
Reason: Cracked screen
Status: Damaged

The asset is ready for repair.
```

## Troubleshooting

### "Error: SNIPEIT_API_KEY environment variable not set"

- Make sure you've set the API key environment variable
- Check that you've exported it in your current terminal session

### "Error: Could not find asset"

- Verify the asset tag is correct
- Check that the asset exists in Snipe-IT
- Ensure your API key has permission to view assets

### "Error creating maintenance"

- Verify the asset ID is valid
- Check that your API key has permission to create maintenances
- If using SUPPLIER_ID, verify it's a valid supplier

### "Error checking in asset"

- Ensure the asset is actually checked out
- Verify your API key has check-in permissions

### "Error updating asset status"

- Verify the DAMAGED_STATUS_ID is correct
- Check that the status exists in your Snipe-IT instance
- Ensure your API key has permission to update assets

## API Permissions Required

Your API key needs the following permissions:

- View assets
- Create maintenances
- Check in assets
- Update assets

## Security Notes

- Keep your API key secure and never commit it to version control
- Use environment variables or a `.env` file (add to `.gitignore`)
- Restrict API key permissions to only what's needed
