"""
Database of Star Wars origin planets, destination routes and travel time in days (between origin and destination)
"""
from pathlib import Path
import sqlite3
def list_all_routes(db_path: Path):
    """List all routes in the universe database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM ROUTES')
    routes = cursor.fetchall()
    
    conn.close()
    return routes

def create_universe_database(db_path: Path):
    """Create and initialize the universe database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ROUTES (
        ORIGIN TEXT NOT NULL,
        DESTINATION TEXT NOT NULL,
        TRAVEL_TIME INTEGER NOT NULL,
        PRIMARY KEY (ORIGIN, DESTINATION)
    )
    ''')
    
    # Sample route data: ORIGIN, DESTINATION, TRAVEL_TIME
    routes = [
        ('Tatooine', 'Dagobah', 6),
        ('Tatooine', 'Hoth', 6),
        ('Dagobah', 'Endor', 4),
        ('Dagobah', 'Hoth', 1),
        ('Hoth', 'Endor', 1)
    ]
    
    # Insert routes
    cursor.executemany('INSERT INTO ROUTES VALUES (?, ?, ?)', routes)
    conn.commit()
    conn.close()
