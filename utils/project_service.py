# -*- coding: utf-8 -*-
"""
Project persistence service using Supabase

Provides functions to save/load projects to/from Supabase database.
If Supabase is not configured, functions return None gracefully.
"""

import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime
from utils.supabase_client import get_supabase, is_supabase_configured


def save_project(name: str, df: pd.DataFrame, description: str = "") -> Optional[str]:
    """
    Save a project to Supabase.

    Args:
        name: Project name
        df: DataFrame with project data
        description: Optional project description

    Returns:
        Project ID (UUID string) if successful, None if Supabase not configured or error

    Raises:
        Exception if database error occurs
    """
    supabase = get_supabase()
    if not supabase:
        print("Warning: Supabase not configured, project not saved")
        return None

    try:
        # Calculate statistics
        total_rows = len(df)
        mapped_rows = len(df[
            df['mapped_scenario'].notna() &
            df['mapped_discipline'].notna() &
            df['mapped_mmi_code'].notna()
        ])
        total_gwp = float(df['total_gwp'].sum())

        # 1. Create project record
        project_data = {
            'name': name,
            'description': description,
            'status': 'active',
            'total_rows': total_rows,
            'mapped_rows': mapped_rows,
            'total_gwp': total_gwp
        }

        result = supabase.table('projects').insert(project_data).execute()

        if not result.data:
            raise Exception("Failed to create project")

        project_id = result.data[0]['id']

        # 2. Prepare rows for bulk insert
        rows_to_insert = []
        for _, row in df.iterrows():
            row_data = {
                'project_id': project_id,
                'row_id': int(row['row_id']),
                'category': str(row['category']) if pd.notna(row['category']) else None,
                'construction_a': float(row['construction_a']) if pd.notna(row['construction_a']) else 0,
                'operation_b': float(row['operation_b']) if pd.notna(row['operation_b']) else 0,
                'end_of_life_c': float(row['end_of_life_c']) if pd.notna(row['end_of_life_c']) else 0,
                'total_gwp': float(row['total_gwp']) if pd.notna(row['total_gwp']) else 0,
                'suggested_scenario': str(row['suggested_scenario']) if pd.notna(row['suggested_scenario']) else None,
                'suggested_discipline': str(row['suggested_discipline']) if pd.notna(row['suggested_discipline']) else None,
                'suggested_mmi_code': str(row['suggested_mmi_code']) if pd.notna(row['suggested_mmi_code']) else None,
                'suggested_mmi_label': str(row['suggested_mmi_label']) if pd.notna(row['suggested_mmi_label']) else None,
                'mapped_scenario': str(row['mapped_scenario']) if pd.notna(row['mapped_scenario']) else None,
                'mapped_discipline': str(row['mapped_discipline']) if pd.notna(row['mapped_discipline']) else None,
                'mapped_mmi_code': str(row['mapped_mmi_code']) if pd.notna(row['mapped_mmi_code']) else None,
                'is_summary': bool(row['is_summary']) if pd.notna(row['is_summary']) else False,
                'excluded': bool(row['excluded']) if pd.notna(row['excluded']) else False
            }
            rows_to_insert.append(row_data)

        # 3. Bulk insert project data (batch to avoid size limits)
        batch_size = 500  # Supabase recommended batch size
        for i in range(0, len(rows_to_insert), batch_size):
            batch = rows_to_insert[i:i + batch_size]
            supabase.table('project_data').insert(batch).execute()

        return project_id

    except Exception as e:
        print(f"Error saving project: {e}")
        raise


def load_project(project_id: str) -> Optional[pd.DataFrame]:
    """
    Load a project from Supabase.

    Args:
        project_id: UUID of the project to load

    Returns:
        DataFrame with project data, or None if not found or error

    Raises:
        Exception if database error occurs
    """
    supabase = get_supabase()
    if not supabase:
        print("Warning: Supabase not configured, cannot load project")
        return None

    try:
        # Fetch all project data rows
        result = supabase.table('project_data')\
            .select('*')\
            .eq('project_id', project_id)\
            .order('row_id')\
            .execute()

        if not result.data:
            return None

        # Convert to DataFrame
        df = pd.DataFrame(result.data)

        # Remove Supabase-specific columns
        columns_to_drop = ['id', 'project_id', 'updated_at']
        df = df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore')

        # Ensure correct data types
        numeric_cols = ['construction_a', 'operation_b', 'end_of_life_c', 'total_gwp']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        boolean_cols = ['is_summary', 'excluded']
        for col in boolean_cols:
            if col in df.columns:
                df[col] = df[col].fillna(False).astype(bool)

        return df

    except Exception as e:
        print(f"Error loading project: {e}")
        raise


def list_projects(limit: int = 50, offset: int = 0) -> Optional[List[Dict[str, Any]]]:
    """
    List recent projects.

    Args:
        limit: Maximum number of projects to return
        offset: Number of projects to skip (for pagination)

    Returns:
        List of project dictionaries, or None if Supabase not configured

    Raises:
        Exception if database error occurs
    """
    supabase = get_supabase()
    if not supabase:
        return None

    try:
        result = supabase.table('projects')\
            .select('*')\
            .order('updated_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()

        return result.data

    except Exception as e:
        print(f"Error listing projects: {e}")
        raise


def update_project_row(project_id: str, row_id: int, updates: Dict[str, Any]) -> bool:
    """
    Update a single row in a project.

    Args:
        project_id: UUID of the project
        row_id: Row ID to update
        updates: Dictionary of column names and new values

    Returns:
        True if successful, False otherwise

    Raises:
        Exception if database error occurs
    """
    supabase = get_supabase()
    if not supabase:
        return False

    try:
        # Add timestamp
        updates['updated_at'] = datetime.now().isoformat()

        result = supabase.table('project_data')\
            .update(updates)\
            .eq('project_id', project_id)\
            .eq('row_id', row_id)\
            .execute()

        return len(result.data) > 0

    except Exception as e:
        print(f"Error updating project row: {e}")
        raise


def delete_project(project_id: str) -> bool:
    """
    Delete a project and all its data.

    Args:
        project_id: UUID of the project to delete

    Returns:
        True if successful, False otherwise

    Note:
        Cascade delete will automatically remove all project_data rows.
    """
    supabase = get_supabase()
    if not supabase:
        return False

    try:
        result = supabase.table('projects')\
            .delete()\
            .eq('id', project_id)\
            .execute()

        return len(result.data) > 0

    except Exception as e:
        print(f"Error deleting project: {e}")
        raise


def update_project_metadata(project_id: str, name: Optional[str] = None,
                           description: Optional[str] = None,
                           status: Optional[str] = None) -> bool:
    """
    Update project metadata.

    Args:
        project_id: UUID of the project
        name: New name (optional)
        description: New description (optional)
        status: New status (optional): 'active', 'completed', 'archived'

    Returns:
        True if successful, False otherwise
    """
    supabase = get_supabase()
    if not supabase:
        return False

    try:
        updates = {'updated_at': datetime.now().isoformat()}

        if name is not None:
            updates['name'] = name
        if description is not None:
            updates['description'] = description
        if status is not None:
            updates['status'] = status

        result = supabase.table('projects')\
            .update(updates)\
            .eq('id', project_id)\
            .execute()

        return len(result.data) > 0

    except Exception as e:
        print(f"Error updating project metadata: {e}")
        raise


def refresh_project_statistics(project_id: str, df: pd.DataFrame) -> bool:
    """
    Recalculate and update project statistics.

    Args:
        project_id: UUID of the project
        df: Current DataFrame with project data

    Returns:
        True if successful, False otherwise
    """
    supabase = get_supabase()
    if not supabase:
        return False

    try:
        total_rows = len(df)
        mapped_rows = len(df[
            df['mapped_scenario'].notna() &
            df['mapped_discipline'].notna() &
            df['mapped_mmi_code'].notna()
        ])
        total_gwp = float(df['total_gwp'].sum())

        updates = {
            'total_rows': total_rows,
            'mapped_rows': mapped_rows,
            'total_gwp': total_gwp,
            'updated_at': datetime.now().isoformat()
        }

        result = supabase.table('projects')\
            .update(updates)\
            .eq('id', project_id)\
            .execute()

        return len(result.data) > 0

    except Exception as e:
        print(f"Error refreshing project statistics: {e}")
        raise
