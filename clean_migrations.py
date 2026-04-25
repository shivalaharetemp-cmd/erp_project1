#!/usr/bin/env python
"""
Clean migration files and Python cache files from the project.
This script removes:
- All migration files (except __init__.py)
- All __pycache__ directories
- All .pyc files
"""

import os
import shutil
import sys

def clean_migrations_and_cache():
    """Remove migration files and Python cache."""
    deleted_migrations = 0
    deleted_pycache_dirs = 0
    deleted_pyc_files = 0
    
    for root, dirs, files in os.walk('.'):
        # Skip virtual environment and hidden directories
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
        
        # Remove migration files (keep __init__.py)
        if 'migrations' in root:
            for file in files:
                if file != '__init__.py' and file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        os.remove(filepath)
                        print(f"Deleted migration: {filepath}")
                        deleted_migrations += 1
                    except OSError as e:
                        print(f"Error deleting {filepath}: {e}")
        
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                print(f"Deleted cache dir: {pycache_path}")
                deleted_pycache_dirs += 1
            except OSError as e:
                print(f"Error deleting {pycache_path}: {e}")
        
        # Remove .pyc files
        for file in files:
            if file.endswith('.pyc'):
                filepath = os.path.join(root, file)
                try:
                    os.remove(filepath)
                    print(f"Deleted: {filepath}")
                    deleted_pyc_files += 1
                except OSError as e:
                    print(f"Error deleting {filepath}: {e}")
    
    print("\n" + "="*50)
    print("CLEANUP COMPLETE")
    print("="*50)
    print(f"Migration files deleted: {deleted_migrations}")
    print(f"__pycache__ directories deleted: {deleted_pycache_dirs}")
    print(f".pyc files deleted: {deleted_pyc_files}")
    print("\nNext steps:")
    print("  1. python manage.py makemigrations")
    print("  2. python manage.py migrate")

if __name__ == '__main__':
    print("Starting cleanup...")
    print("-" * 50)
    clean_migrations_and_cache()
