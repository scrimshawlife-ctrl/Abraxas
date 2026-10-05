"""Database initialization script for PostgreSQL adapter"""
import asyncio
import asyncpg
import os
from typing import Optional

async def init_database(dsn: Optional[str] = None):
    """Initialize the database schema for Abraxas domain data"""
    if dsn is None:
        dsn = os.getenv('ABRAXAS_POSTGRES_DSN', 'postgresql://user:pass@localhost/abraxas')
    
    conn = await asyncpg.connect(dsn)
    try:
        # Create tables if they don't exist
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS domain_signals (
                id SERIAL PRIMARY KEY,
                domain VARCHAR(255) NOT NULL,
                signal_type VARCHAR(100),
                signal_value JSONB,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                source VARCHAR(100),
                confidence FLOAT DEFAULT 1.0
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS phase_transitions (
                id SERIAL PRIMARY KEY,
                domain VARCHAR(255) NOT NULL,
                from_phase VARCHAR(50),
                to_phase VARCHAR(50),
                transition_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                trigger VARCHAR(255),
                metadata JSONB
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS oracle_runs (
                id SERIAL PRIMARY KEY,
                run_id VARCHAR(255) UNIQUE,
                oracle_name VARCHAR(100),
                input_data JSONB,
                output_data JSONB,
                status VARCHAR(50),
                started_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                duration_ms INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS ritual_executions (
                id SERIAL PRIMARY KEY,
                ritual_id VARCHAR(255) UNIQUE,
                ritual_name VARCHAR(100),
                domain VARCHAR(255),
                parameters JSONB,
                results JSONB,
                status VARCHAR(50),
                started_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS timechain_status (
                id SERIAL PRIMARY KEY,
                block_height INTEGER,
                block_hash VARCHAR(64),
                merkle_root VARCHAR(64),
                timestamp TIMESTAMP WITH TIME ZONE,
                node_count INTEGER,
                network_status VARCHAR(50),
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        ''')
        
        # Create indexes for better query performance
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_domain_signals_domain_timestamp 
            ON domain_signals(domain, timestamp DESC)
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_phase_transitions_domain_time 
            ON phase_transitions(domain, transition_time DESC)
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_oracle_runs_time 
            ON oracle_runs(completed_at DESC)
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_ritual_executions_domain_time 
            ON ritual_executions(domain, completed_at DESC)
        ''')
        
        print("✓ Database schema initialized successfully")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(init_database())