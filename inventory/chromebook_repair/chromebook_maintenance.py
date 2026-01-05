#!/usr/bin/env python3
"""
Chromebook Maintenance Workflow Script
Handles the complete workflow for repairing a Chromebook with maintenance issues.
"""

import requests
import sys
import os
from typing import Optional, Dict, Any
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


class SnipeITClient:
    """Client for interacting with Snipe-IT API"""

    def __init__(self, base_url: str, api_key: str):
        """
        Initialize Snipe-IT client

        Args:
            base_url: Base URL of Snipe-IT instance (e.g., https://your-instance.snipe-it.io/api/v1)
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def get_asset_by_tag(self, asset_tag: str) -> Optional[Dict[str, Any]]:
        """
        Get asset information by asset tag

        Args:
            asset_tag: The asset tag identifier

        Returns:
            Asset data if found, None otherwise
        """
        url = f'{self.base_url}/hardware/bytag/{asset_tag}'
        print("using url", url)

        try:
            response = requests.get(url, headers=self.headers)
            # print(response.status_code)
            response.raise_for_status()
            data = response.json()
            # print(data)

            if response.status_code == 200:
                return data
            else:
                print(f"Error: {data.get('messages', 'Unknown error')}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching asset: {e}")
            return None

    def create_maintenance(self, asset_id: int, title: str, notes: str,
                          supplier_id: int) -> bool:
        """
        Create a maintenance record for an asset

        Args:
            asset_id: ID of the asset
            title: Title/type of maintenance
            notes: Detailed notes about the maintenance
            supplier_id: Optional supplier ID

        Returns:
            True if successful, False otherwise
        """
        url = f'{self.base_url}/maintenances'
        today = datetime.now()
        month = f"{today.month:02d}"
        day = f"{today.day:02d}"
        formatted_date = "-".join([str(today.year), month, day])

        payload = {
            'asset_id': asset_id,
            'title': title,
            'name': title,
            'supplier_id': supplier_id,
            'notes': notes,
            'asset_maintenance_type': 'Repair',
            'start_date': formatted_date
        }

        # if supplier_id:
        #     payload['supplier_id'] = supplier_id

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 'success':
                print(f"✓ Maintenance created successfully (ID: {data.get('payload', {}).get('id', 'N/A')})")
                return True
            else:
                print(f"Error creating maintenance: {data.get('messages', 'Unknown error')}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Error creating maintenance: {e}")
            return False

    def checkin_asset(self, asset_id: int, note: str) -> bool:
        """
        Check in an asset

        Args:
            asset_id: ID of the asset
            note: Note for check-in

        Returns:
            True if successful, False otherwise
        """
        url = f'{self.base_url}/hardware/{asset_id}/checkin'

        payload = {
            'note': note
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 'success':
                print(f"✓ Asset checked in successfully")
                return True
            else:
                print(f"Error checking in asset: {data.get('messages', 'Unknown error')}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Error checking in asset: {e}")
            return False

    def update_asset_status(self, asset_id: int, status_id: int) -> bool:
        """
        Update asset status

        Args:
            asset_id: ID of the asset
            status_id: ID of the status to set

        Returns:
            True if successful, False otherwise
        """
        url = f'{self.base_url}/hardware/{asset_id}'

        payload = {
            'status_id': status_id
        }

        try:
            response = requests.patch(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 'success':
                print(f"✓ Asset status updated to 'Damaged'")
                return True
            else:
                print(f"Error updating asset status: {data.get('messages', 'Unknown error')}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Error updating asset status: {e}")
            return False


def main():
    """Main workflow function"""

    # Configuration - set these as environment variables or update directly
    BASE_URL = os.getenv('SNIPEIT_BASE_URL', 'https://your-instance.snipe-it.io/api/v1')
    API_KEY = os.getenv('SNIPEIT_API_KEY', '')
    DAMAGED_STATUS_ID = int(os.getenv('SNIPEIT_DAMAGED_STATUS_ID', '0'))
    SUPPLIER_ID = os.getenv('SNIPEIT_SUPPLIER_ID', None)

    if not API_KEY:
        print("Error: SNIPEIT_API_KEY environment variable not set")
        print("Please set it with: export SNIPEIT_API_KEY='your-api-key'")
        sys.exit(1)

    if DAMAGED_STATUS_ID == 0:
        print("Error: SNIPEIT_DAMAGED_STATUS_ID environment variable not set")
        print("Please set it with: export SNIPEIT_DAMAGED_STATUS_ID='your-status-id'")
        sys.exit(1)

    # Initialize client
    client = SnipeITClient(BASE_URL, API_KEY)

    # Prompt for input
    print("=" * 60)
    print("Chromebook Maintenance Workflow")
    print("=" * 60)

    asset_tag = input("\nEnter asset tag: ").strip()
    if not asset_tag:
        print("Error: Asset tag cannot be empty")
        sys.exit(1)

    maintenance_reason = input("Enter maintenance reason (e.g., Cracked screen): ").strip()
    if not maintenance_reason:
        print("Error: Maintenance reason cannot be empty")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Starting maintenance workflow...")
    print("=" * 60 + "\n")

    # Step 1: Find the asset
    print(f"[1/4] Fetching asset with tag: {asset_tag}")
    asset_data = client.get_asset_by_tag(asset_tag)

    if not asset_data:
        print("Error: Could not find asset")
        sys.exit(1)

    asset = asset_data.get('rows', [{}])[0] if asset_data.get('rows') else asset_data
    asset_id = asset.get('id')
    asset_name = asset.get('name', 'Unknown')
    is_checked_out = asset.get('assigned_to') is not None

    print(f"✓ Found asset: {asset_name} (ID: {asset_id})")
    print(f"  Status: {'Checked out' if is_checked_out else 'Available'}")

    # Step 2: Create maintenance record
    print(f"\n[2/4] Creating maintenance record...")
    supplier_id_int = int(SUPPLIER_ID) if SUPPLIER_ID else None
    maintenance_created = client.create_maintenance(
        asset_id=asset_id,
        title=maintenance_reason,
        notes=f"Maintenance created for: {maintenance_reason}",
        supplier_id=supplier_id_int
    )

    if not maintenance_created:
        print("Warning: Failed to create maintenance record, continuing...")

    # Step 3: Check in asset if checked out
    if is_checked_out:
        print(f"\n[3/4] Asset is checked out, checking in...")
        checked_in = client.checkin_asset(
            asset_id=asset_id,
            note=f"Checked in for maintenance: {maintenance_reason}"
        )

        if not checked_in:
            print("Warning: Failed to check in asset, continuing...")
    else:
        print(f"\n[3/4] Asset is not checked out, skipping check-in")

    # Step 4: Update status to Damaged
    print(f"\n[4/4] Updating asset status to 'Damaged'...")
    status_updated = client.update_asset_status(
        asset_id=asset_id,
        status_id=DAMAGED_STATUS_ID
    )

    if not status_updated:
        print("Error: Failed to update asset status")
        sys.exit(1)

    # Success summary
    print("\n" + "=" * 60)
    print("Workflow completed successfully!")
    print("=" * 60)
    print(f"\nAsset: {asset_name} ({asset_tag})")
    print(f"Reason: {maintenance_reason}")
    print(f"Status: Damaged")
    print("\nThe asset is ready for repair.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nWorkflow cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
