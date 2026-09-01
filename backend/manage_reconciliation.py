#!/usr/bin/env python
"""CLI management tool for Qdrant/SQL reconciliation.

Usage:
    python manage_reconciliation.py audit
    python manage_reconciliation.py repair [--fix-embeddings] [--delete-orphaned]
    python manage_reconciliation.py --help
"""

import argparse
import json
from pathlib import Path
import sys

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from services.reconciliation_service import get_reconciliation_service
from core.logging import logger


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Reconcile Qdrant vector embeddings with SQL documents"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Audit subcommand
    audit_parser = subparsers.add_parser("audit", help="Audit SQL and Qdrant for inconsistencies (read-only)")
    audit_parser.add_argument("--json", action="store_true", help="Output report as JSON")
    
    # Repair subcommand
    repair_parser = subparsers.add_parser("repair", help="Repair SQL/Qdrant inconsistencies")
    repair_parser.add_argument(
        "--fix-embeddings",
        action="store_true",
        default=True,
        help="Re-generate missing embeddings (default: True)"
    )
    repair_parser.add_argument(
        "--skip-fix-embeddings",
        action="store_false",
        dest="fix_embeddings",
        help="Skip re-generating missing embeddings"
    )
    repair_parser.add_argument(
        "--delete-orphaned",
        action="store_true",
        default=False,
        help="Delete orphaned vectors from Qdrant (DANGEROUS! default: False)"
    )
    repair_parser.add_argument("--json", action="store_true", help="Output report as JSON")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    service = get_reconciliation_service()
    
    try:
        if args.command == "audit":
            logger.info("Running reconciliation audit...")
            report = service.audit()
            
            if args.json:
                print(json.dumps(report.to_dict(), indent=2))
            else:
                print_audit_report(report)
        
        elif args.command == "repair":
            if args.delete_orphaned:
                print("\n⚠️  WARNING: --delete-orphaned flag will permanently delete vectors from Qdrant!")
                confirm = input("Type 'yes' to confirm: ").strip().lower()
                if confirm != "yes":
                    print("Repair cancelled.")
                    sys.exit(0)
            
            logger.info("Running reconciliation repair...")
            report = service.repair(
                missing_embeddings=args.fix_embeddings,
                delete_orphaned=args.delete_orphaned
            )
            
            if args.json:
                print(json.dumps(report.to_dict(), indent=2))
            else:
                print_repair_report(report)
    
    except Exception as e:
        logger.error(f"Reconciliation failed: {str(e)}")
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def print_audit_report(report):
    """Pretty-print audit report."""
    print("\n" + "=" * 70)
    print("RECONCILIATION AUDIT REPORT")
    print("=" * 70)
    
    print(f"\nTimestamp: {report.timestamp.isoformat()}")
    print(f"\n{'Summary':^70}")
    print("-" * 70)
    print(f"  SQL Documents:       {report.sql_documents}")
    print(f"  Qdrant Vectors:      {report.qdrant_vectors}")
    print(f"  Missing Embeddings:  {len(report.missing_embeddings)}")
    print(f"  Orphaned Vectors:    {len(report.orphaned_embeddings)}")
    print(f"  Errors:              {len(report.errors)}")
    
    if report.missing_embeddings:
        print(f"\n{'Missing Embeddings':^70}")
        print("-" * 70)
        for item in report.missing_embeddings:
            print(f"  • {item['filename']} (ID: {item['document_id'][:8]}...)")
            print(f"    Chunks: {item['chunk_count']}, Workspace: {item['workspace_id'][:8]}...")
    
    if report.orphaned_embeddings:
        print(f"\n{'Orphaned Vectors (in Qdrant but not in SQL)':^70}")
        print("-" * 70)
        for doc_id in report.orphaned_embeddings[:10]:
            print(f"  • {doc_id}")
        if len(report.orphaned_embeddings) > 10:
            print(f"  ... and {len(report.orphaned_embeddings) - 10} more")
    
    if report.errors:
        print(f"\n{'Errors':^70}")
        print("-" * 70)
        for error in report.errors:
            print(f"  ❌ {error}")
    
    print("\n" + "=" * 70 + "\n")


def print_repair_report(report):
    """Pretty-print repair report."""
    print("\n" + "=" * 70)
    print("RECONCILIATION REPAIR REPORT")
    print("=" * 70)
    
    print(f"\nTimestamp: {report.timestamp.isoformat()}")
    print(f"\n{'Summary':^70}")
    print("-" * 70)
    print(f"  Documents Repaired:  {report.repaired_count}")
    print(f"  Vectors Deleted:     {report.deleted_count}")
    print(f"  Errors:              {len(report.errors)}")
    
    if report.repaired_count > 0:
        print(f"\n✅ Re-embedded {report.repaired_count} document(s)")
    
    if report.deleted_count > 0:
        print(f"\n⚠️  Deleted {report.deleted_count} orphaned vector set(s)")
    
    if report.errors:
        print(f"\n{'Errors':^70}")
        print("-" * 70)
        for error in report.errors:
            print(f"  ❌ {error}")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
