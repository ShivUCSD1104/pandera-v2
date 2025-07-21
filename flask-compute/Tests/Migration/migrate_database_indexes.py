"""
Database migration script to add performance optimization indexes.

This script adds composite indexes to improve query performance for
the Greeks Landscape feature and other database operations.
"""

import logging
import sys
import os
from sqlalchemy import text, inspect

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from db import engine, Base, OptionData, UnderlyingData, YieldData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseIndexMigration:
    """
    Handles database index migration for performance optimization.
    """
    
    def __init__(self):
        self.engine = engine
        self.inspector = inspect(engine)
        
    def check_existing_indexes(self, table_name: str) -> dict:
        """
        Check what indexes already exist on a table.
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            Dictionary of existing indexes
        """
        try:
            existing_indexes = self.inspector.get_indexes(table_name)
            index_dict = {idx['name']: idx for idx in existing_indexes}
            logger.info(f"Found {len(existing_indexes)} existing indexes on {table_name}")
            return index_dict
        except Exception as e:
            logger.warning(f"Could not check existing indexes for {table_name}: {str(e)}")
            return {}
    
    def create_index_if_not_exists(self, index_name: str, table_name: str, columns: list):
        """
        Create an index if it doesn't already exist.
        
        Args:
            index_name: Name of the index to create
            table_name: Name of the table
            columns: List of column names for the index
        """
        try:
            existing_indexes = self.check_existing_indexes(table_name)
            
            if index_name in existing_indexes:
                logger.info(f"Index {index_name} already exists on {table_name}")
                return True
            
            # Create the index
            columns_str = ', '.join(columns)
            sql = f"CREATE INDEX {index_name} ON {table_name} ({columns_str})"
            
            logger.info(f"Creating index: {sql}")
            
            with self.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            
            logger.info(f"Successfully created index {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {str(e)}")
            return False
    
    def migrate_option_data_indexes(self):
        """Create performance indexes for option_data table."""
        logger.info("Migrating option_data table indexes")
        
        indexes_to_create = [
            ('idx_option_ticker_expiry', 'option_data', ['ticker', 'expiration_date']),
            ('idx_option_ticker_type', 'option_data', ['ticker', 'option_type']),
            ('idx_option_ticker_strike', 'option_data', ['ticker', 'strike']),
            ('idx_option_ticker_expiry_type', 'option_data', ['ticker', 'expiration_date', 'option_type']),
            ('idx_option_fetch_date', 'option_data', ['fetch_date']),
        ]
        
        success_count = 0
        for index_name, table_name, columns in indexes_to_create:
            if self.create_index_if_not_exists(index_name, table_name, columns):
                success_count += 1
        
        logger.info(f"Created {success_count}/{len(indexes_to_create)} indexes for option_data")
        return success_count == len(indexes_to_create)
    
    def migrate_underlying_data_indexes(self):
        """Create performance indexes for underlying_data table."""
        logger.info("Migrating underlying_data table indexes")
        
        indexes_to_create = [
            ('idx_underlying_ticker_date', 'underlying_data', ['ticker', 'date']),
            ('idx_underlying_fetch_date', 'underlying_data', ['fetch_date']),
        ]
        
        success_count = 0
        for index_name, table_name, columns in indexes_to_create:
            if self.create_index_if_not_exists(index_name, table_name, columns):
                success_count += 1
        
        logger.info(f"Created {success_count}/{len(indexes_to_create)} indexes for underlying_data")
        return success_count == len(indexes_to_create)
    
    def migrate_yield_data_indexes(self):
        """Create performance indexes for yield_data table."""
        logger.info("Migrating yield_data table indexes")
        
        indexes_to_create = [
            ('idx_yield_ticker_date', 'yield_data', ['ticker', 'date']),
            ('idx_yield_label_date', 'yield_data', ['label', 'date']),
            ('idx_yield_fetch_date', 'yield_data', ['fetch_date']),
        ]
        
        success_count = 0
        for index_name, table_name, columns in indexes_to_create:
            if self.create_index_if_not_exists(index_name, table_name, columns):
                success_count += 1
        
        logger.info(f"Created {success_count}/{len(indexes_to_create)} indexes for yield_data")
        return success_count == len(indexes_to_create)
    
    def run_full_migration(self):
        """Run the complete database index migration."""
        logger.info("Starting database index migration for performance optimization")
        
        try:
            # Check database connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("Database connection successful")
            
            # Migrate each table
            results = {
                'option_data': self.migrate_option_data_indexes(),
                'underlying_data': self.migrate_underlying_data_indexes(),
                'yield_data': self.migrate_yield_data_indexes(),
            }
            
            # Summary
            successful_tables = sum(1 for success in results.values() if success)
            total_tables = len(results)
            
            logger.info(f"Migration completed: {successful_tables}/{total_tables} tables migrated successfully")
            
            if successful_tables == total_tables:
                logger.info("✅ All database indexes created successfully!")
                return True
            else:
                logger.warning("⚠️  Some indexes failed to create. Check logs for details.")
                return False
                
        except Exception as e:
            logger.error(f"Database migration failed: {str(e)}")
            return False
    
    def verify_indexes(self):
        """Verify that all expected indexes exist."""
        logger.info("Verifying database indexes")
        
        expected_indexes = {
            'option_data': [
                'idx_option_ticker_expiry',
                'idx_option_ticker_type', 
                'idx_option_ticker_strike',
                'idx_option_ticker_expiry_type',
                'idx_option_fetch_date'
            ],
            'underlying_data': [
                'idx_underlying_ticker_date',
                'idx_underlying_fetch_date'
            ],
            'yield_data': [
                'idx_yield_ticker_date',
                'idx_yield_label_date',
                'idx_yield_fetch_date'
            ]
        }
        
        verification_results = {}
        
        for table_name, expected_index_list in expected_indexes.items():
            existing_indexes = self.check_existing_indexes(table_name)
            
            found_indexes = []
            missing_indexes = []
            
            for expected_index in expected_index_list:
                if expected_index in existing_indexes:
                    found_indexes.append(expected_index)
                else:
                    missing_indexes.append(expected_index)
            
            verification_results[table_name] = {
                'expected': len(expected_index_list),
                'found': len(found_indexes),
                'missing': missing_indexes,
                'success': len(missing_indexes) == 0
            }
            
            if missing_indexes:
                logger.warning(f"Missing indexes on {table_name}: {missing_indexes}")
            else:
                logger.info(f"✅ All indexes verified on {table_name}")
        
        # Overall verification result
        all_successful = all(result['success'] for result in verification_results.values())
        
        if all_successful:
            logger.info("✅ All database indexes verified successfully!")
        else:
            logger.warning("⚠️  Some indexes are missing. Run migration again.")
        
        return all_successful, verification_results
    
    def get_index_usage_stats(self):
        """Get statistics about index usage (PostgreSQL specific)."""
        try:
            # This query works for PostgreSQL - adapt for other databases
            sql = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes 
            WHERE schemaname = 'public'
            ORDER BY idx_tup_read DESC;
            """
            
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                stats = result.fetchall()
                
                logger.info("Index usage statistics:")
                for row in stats:
                    logger.info(f"  {row.tablename}.{row.indexname}: {row.idx_tup_read} reads, {row.idx_tup_fetch} fetches")
                
                return stats
                
        except Exception as e:
            logger.info(f"Could not get index usage stats (database may not support it): {str(e)}")
            return []


def main():
    """Main function to run database migration."""
    try:
        migration = DatabaseIndexMigration()
        
        print("="*60)
        print("DATABASE INDEX MIGRATION FOR PERFORMANCE OPTIMIZATION")
        print("="*60)
        
        # Run migration
        success = migration.run_full_migration()
        
        if success:
            print("\n✅ Migration completed successfully!")
            
            # Verify indexes
            print("\nVerifying indexes...")
            verified, results = migration.verify_indexes()
            
            if verified:
                print("✅ All indexes verified!")
            else:
                print("⚠️  Some indexes missing - check logs")
            
            # Try to get usage stats
            print("\nGetting index usage statistics...")
            migration.get_index_usage_stats()
            
        else:
            print("\n❌ Migration failed - check logs for details")
            return 1
        
        print("\n" + "="*60)
        print("Migration completed!")
        print("="*60)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Migration script failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)