from flask import Flask, request, jsonify, render_template
import sqlite3
import json
from pathlib import Path
import os
from typing import Dict, List, Set, Tuple, Optional
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import matplotlib.animation as animation
from typing import Dict, List, Set, Tuple
import numpy as np
from millennium_falcon import MillenniumFalcon
from database_tools import create_universe_database

"""
Purpose: Flask backend (web server)
Assignment title: The "Millennium Falcon onboard computer"
"""


app = Flask(__name__)

# Create required directories
UPLOAD_FOLDER = Path('uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Configure Flask app
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        if 'millennium' not in request.files or 'empire' not in request.files:
            return jsonify({'success': False, 'error': 'Missing required files'})

        millennium_file = request.files['millennium']
        empire_file = request.files['empire']

        # Create safe file paths
        millennium_path = UPLOAD_FOLDER / 'millennium-falcon.json'
        empire_path = UPLOAD_FOLDER / 'empire.json'

        # Save uploaded files
        millennium_file.save(millennium_path)
        empire_file.save(empire_path)

        # Calculate odds
        falcon = MillenniumFalcon(str(millennium_path))
        odds, debug_info = falcon.calculate_odds_with_debug(str(empire_path))

        # # Generate visualization
        # visualization_path = UPLOAD_FOLDER / 'mission_visualization.png'
        # falcon.visualize_mission_dynamic(str(empire_path), odds)

        return jsonify({
            'success': True,
            'odds': odds,
            'debug_info': debug_info
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})



if __name__ == '__main__':
    # Ensure upload directory exists
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    
    # Create initial database if it doesn't exist
    db_path = UPLOAD_FOLDER / 'universe.db'
    # if not db_path.exists():
    #     create_universe_database(db_path)
    
    app.run(debug=True)
