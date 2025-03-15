import pdb
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import matplotlib.animation as animation
import numpy as np


class MillenniumFalcon:
    def __init__(self, config_file: str):
        self.routes: Dict[str, Dict[str, int]] = {}
        self.autonomy: int = 0
        self.departure: str = ""
        self.arrival: str = ""
        
        try:
            db_path = self.load_config_data(config_file)
            
            if not db_path.exists():
                raise FileNotFoundError(f"Database file not found: {db_path}")
                
            self.routes = self._load_routes(db_path)
            
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in configuration file")
        except KeyError as e:
            raise ValueError(f"Missing required configuration key: {e}")

    def load_config_data(self, config_file):
        """
        This is responsible for loading configuration data from a JSON file and setting up the necessary attributes 
        for the class instance. The method opens the specified configuration file in read mode, parses the JSON data, 
        and assigns values to the instance variables `self.autonomy`, `self.departure`, and `self.arrival`, which 
        represent the maximum distance the Millennium Falcon can travel without refueling, the starting planet, and 
        the destination planet, respectively. It then determines the directory containing the configuration file using 
        the `Path` class from the `pathlib` module and constructs the path to the database file containing the travel 
        routes by combining this directory with the value associated with the 'routes_db' key in the configuration file. 
        The method returns the constructed database path (`db_path`) for further processing.
        """
        with open(config_file, 'r') as f:
            config = json.load(f)
                
        self.autonomy = config['autonomy']
        self.departure = config['departure']
        self.arrival = config['arrival']
            
        # Get the directory containing the config file
        config_dir = Path(config_file).parent
        db_path = config_dir / config['routes_db']
        return db_path

    def _load_routes(self, db_path: Path) -> Dict[str, Dict[str, int]]:
        """
        The `routes` dictionary is initialized to store the travel times between different planets.
        The dictionary is structured such that each key is a planet name, and the value is another
        dictionary where the keys are destination planets and the values are the travel times to
        those destinations.
        """
        if not db_path.exists():
            raise FileNotFoundError(f"Database file not found: {db_path}")
            
        routes: Dict[str, Dict[str, int]] = {}
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT origin, destination, travel_time FROM ROUTES')
            for origin, destination, travel_time in cursor.fetchall():
                if origin not in routes:
                    routes[origin] = {}
                if destination not in routes:
                    routes[destination] = {}
                    
                routes[origin][destination] = travel_time
                routes[destination][origin] = travel_time
                
            conn.close()
            return routes
            
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
            
    def _get_possible_paths(self, countdown: int) -> List[List[Tuple[str, int, str]]]:
        """
        This method generates all possible paths for the mission given a countdown value.
        This method uses a depth-first search (DFS) algorithm to explore all potential routes 
        from the departure planet to the arrival planet within the given time constraints.

        The _get_possible_paths method initializes an empty list to store the paths and a set 
        to keep track of visited nodes. The DFS function is defined within this method to 
        recursively explore each possible path. It checks if the current time spent exceeds 
        the countdown, and if so, it returns without adding the path. If the current planet 
        is the arrival planet, it appends the path to the list of paths and returns.

        The DFS function iterates over the neighboring planets and their respective travel times. 
        If the travel time exceeds the remaining fuel, it calculates the days required to refuel 
        and travel, ensuring these actions fit within the countdown. It then adds the refuel and 
        travel actions to the path and recursively calls DFS for the next planet. If the travel 
        time is within the remaining fuel, it directly adds the travel action to the path and 
        calls DFS for the next planet. After exploring each path, it backtracks by removing the 
        last actions and updating the visited set.
        """
        paths: List[List[Tuple[str, int, str]]] = []  # (planet, day, action)
        visited: Set[Tuple[str, int]] = set()
        
        def dfs(current: str, path: List[Tuple[str, int, str]], time_spent: int, fuel: int) -> None:
            if time_spent > countdown:
                return
                
            if current == self.arrival:
                paths.append(path[:])
                return
                
            for next_planet, travel_time in self.routes[current].items():
                if travel_time > fuel:
                    # Need to refuel first
                    refuel_day = time_spent + 1
                    travel_day = refuel_day + travel_time
                    new_fuel = self.autonomy - travel_time
                    
                    if travel_day <= countdown and (next_planet, travel_day) not in visited:
                        visited.add((next_planet, travel_day))
                        # Add both the refuel day and travel day
                        path.append((current, refuel_day, "REFUEL"))
                        path.append((current, travel_day - travel_time, "WAIT"))  # Day before travel
                        path.append((next_planet, travel_day, "TRAVEL"))
                        dfs(next_planet, path, travel_day, new_fuel)
                        path.pop()
                        path.pop()
                        path.pop()
                        visited.remove((next_planet, travel_day))
                else:
                    new_time = time_spent + travel_time
                    new_fuel = fuel - travel_time
                    if new_time <= countdown and (next_planet, new_time) not in visited:
                        visited.add((next_planet, new_time))
                        path.append((next_planet, new_time, "TRAVEL"))
                        dfs(next_planet, path, new_time, new_fuel)
                        path.pop()
                        visited.remove((next_planet, new_time))
        
        dfs(self.departure, [(self.departure, 0, "START")], 0, self.autonomy)
        return paths

    def calculate_odds(self, empire_file: str) -> float:
        """
        Calculate the odds of successfully navigating the Millennium Falcon without being captured by bounty hunters.
        Args:
            empire_file (str): The path to the JSON file containing empire data, including countdown and bounty hunters information.
        Returns:
            float: The probability of successfully navigating without capture, as a percentage.
        """
        with open(empire_file, 'r') as f:
            empire_data = json.load(f)
            
        countdown: int = empire_data['countdown']
        bounty_hunters: Set[Tuple[str, int]] = {
            (hunter['planet'], hunter['day']) 
            for hunter in empire_data['bounty_hunters']
        }
        print(f"hunters: {bounty_hunters}")
        
        # pdb.set_trace() # dbg

        possible_paths = self._get_possible_paths(countdown)
        print(possible_paths)
        if not possible_paths:
            return 0.0
        
        best_probability: float = 0.0
        for path_index, path in enumerate(possible_paths, 1):
            # Check encounters with bounty hunters
            encounters = []
            for planet, day, action in path:
                if (planet, day) in bounty_hunters:
                    encounters.append(f"  - Day {day}: Bounty hunter encounter on {planet} during {action}")
            
            encounter_count = len(encounters)
                
            if encounter_count == 0:
                return 100.0
                
            # Calculate probability
            success_probability = (0.9 ** encounter_count) * 100
            
            if success_probability > best_probability:
                best_probability = success_probability
        
        return best_probability


    def calculate_odds_with_debug(self, empire_file: str) -> Tuple[float, str]:
        """
        Calculate the odds of successfully navigating the Millennium Falcon without being caught by bounty hunters,
        with detailed debug information.
        Args:
            empire_file (str): The path to the JSON file containing empire intelligence data.
        Returns:
            Tuple[float, str]: A tuple containing the success probability (as a percentage) and a debug string with detailed information.
        """
        with open(empire_file, 'r') as f:
            empire_data = json.load(f)
            
        countdown: int = empire_data['countdown']
        bounty_hunters: Set[Tuple[str, int]] = {
            (hunter['planet'], hunter['day']) 
            for hunter in empire_data['bounty_hunters']
        }
        
        debug_info = []
        debug_info.append("Empire Intelligence Data:")
        debug_info.append(f"Countdown: {countdown} days")
        debug_info.append("Bounty Hunters:")
        for hunter in empire_data['bounty_hunters']:
            debug_info.append(f"  - Planet: {hunter['planet']}, Day: {hunter['day']}")
        debug_info.append("\n")
        
        possible_paths = self._get_possible_paths(countdown)
        
        if not possible_paths:
            return 0.0, "No possible paths found"
            
        best_probability: float = 0.0
        best_path_debug = ""
        
        for path_index, path in enumerate(possible_paths, 1):
            debug_info.append(f"\nPath {path_index}:")
            debug_info.append("Day-by-day movement:")
            for planet, day, action in path:
                debug_info.append(f"  Day {day}: {action} at {planet}")
                
            # Check encounters with bounty hunters
            encounters = []
            for planet, day, action in path:
                if (planet, day) in bounty_hunters:
                    encounters.append(f"  - Day {day}: Bounty hunter encounter on {planet} during {action}")
            
            encounter_count = len(encounters)
            
            debug_info.append("\nBounty Hunter Encounters:")
            if encounters:
                debug_info.extend(encounters)
                debug_info.append(f"Total encounters: {encounter_count}")
            else:
                debug_info.append("  None")
                
            if encounter_count == 0:
                debug_info.append("\nNo bounty hunters - 100% success rate")
                return 100.0, "\n".join(debug_info)
                
            # Calculate probability
            success_probability = (0.9 ** encounter_count) * 100
            
            debug_info.append(f"\nProbability Calculation:")
            debug_info.append(f"Number of encounters: {encounter_count}")
            debug_info.append(f"Formula: (9/10)^{encounter_count} * 100")
            debug_info.append(f"Success probability = {success_probability:.2f}%")
            
            if success_probability > best_probability:
                best_probability = success_probability
                best_path_debug = "\n".join(debug_info)
        
        return best_probability, best_path_debug


    def visualize_mission_dynamic(self, empire_file: str, odds: float) -> None:
        """Create an interactive visual representation of the mission with dynamic node labeling."""
        # Create figure with extra space at bottom for timeline
        fig = plt.figure(figsize=(15, 12))
        main_ax = plt.subplot2grid((5, 1), (0, 0), rowspan=4)
        timeline_ax = plt.subplot2grid((5, 1), (4, 0))
        
        # Create graph and add planet nodes at fixed positions
        G = nx.Graph()
        planet_positions = {
            'Tatooine': (0, 0),
            'Dagobah': (2, 1),
            'Hoth': (4, 1),
            'Endor': (6, 0)
        }
        
        for planet, pos in planet_positions.items():
            G.add_node(planet, pos=pos, name=planet)
        
        # Add edges (routes) from self.routes
        for origin in self.routes:
            for dest, time in self.routes[origin].items():
                G.add_edge(origin, dest, weight=time)
        
        # Load empire data and bounty hunter information
        with open(empire_file, 'r') as f:
            empire_data = json.load(f)
        
        bounty_hunters = {
            (hunter['planet'], hunter['day']) 
            for hunter in empire_data['bounty_hunters']
        }
        
        # Determine best path based on mission countdown and bounty hunter encounters
        possible_paths = self._get_possible_paths(empire_data['countdown'])
        best_path = None
        best_probability = 0.0
        for path in possible_paths:
            encounters = sum(1 for planet, day, _ in path if (planet, day) in bounty_hunters)
            probability = (0.9 ** encounters) * 100
            if probability > best_probability:
                best_probability = probability
                best_path = path

        # Set title of the main mission map
        main_ax.set_title(f"Millennium Falcon Mission Map\nSuccess Probability: {odds:.1f}%", pad=20)
        pos = nx.get_node_attributes(G, 'pos')
        
        # Draw basic graph structure on the main axis
        nx.draw_networkx_edges(G, pos, edge_color='gray', width=1, alpha=0.5, ax=main_ax)
        nx.draw_networkx_edge_labels(G, pos,
                                    edge_labels=nx.get_edge_attributes(G, 'weight'),
                                    ax=main_ax)
        # Capture the nodes collection to allow for dynamic interactivity
        nodes_collection = nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=1000, ax=main_ax)
        nx.draw_networkx_labels(G, pos, ax=main_ax)
        
        # Highlight the best path, if available
        if best_path:
            path_edges = []
            for i in range(len(best_path) - 1):
                current = best_path[i][0]
                next_planet = best_path[i+1][0]
                if (current, next_planet) in G.edges() or (next_planet, current) in G.edges():
                    path_edges.append((current, next_planet))
            nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color='green', width=2, ax=main_ax)
        
            # Highlight planets with bounty hunter encounters
            hunter_planets = {planet for planet, day in bounty_hunters}
            nx.draw_networkx_nodes(G, pos, nodelist=hunter_planets, node_color='red', node_size=1000, ax=main_ax)
        
        # Create a dynamic annotation for nodes (planets) on the mission map
        annot = main_ax.annotate("", xy=(0, 0), xytext=(20, 20),
                                textcoords="offset points", bbox=dict(boxstyle="round", fc="w"),
                                arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        # Update annotation text and position based on hovered node.
        def update_annot(ind):
            index = ind["ind"][0]
            # Get the corresponding planet based on the order of nodes in G.nodes
            node = list(G.nodes)[index]
            annot.xy = pos[node]
            text = f"Planet: {node}"
            # Optionally show bounty hunter days if present on this planet
            hunter_days = [str(day) for (planet, day) in bounty_hunters if planet == node]
            if hunter_days:
                text += f"\nBounty Hunter(s) on Day(s): {', '.join(hunter_days)}"
            annot.set_text(text)
            annot.get_bbox_patch().set_facecolor("lightyellow")
            annot.get_bbox_patch().set_alpha(0.8)
        
        # Hover event to show/hide dynamic annotations
        def hover(event):
            if event.inaxes == main_ax:
                contains, ind = nodes_collection.contains(event)
                if contains:
                    update_annot(ind)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                elif annot.get_visible():
                    annot.set_visible(False)
                    fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)
        
        # Configure timeline axis
        timeline_ax.set_title('Mission Timeline')
        timeline_ax.set_xlim(-0.5, empire_data['countdown'] + 0.5)
        timeline_ax.set_ylim(0, 1)
        timeline_ax.set_xticks(range(empire_data['countdown'] + 1))
        timeline_ax.set_xticklabels([f'Day {i}' for i in range(empire_data['countdown'] + 1)])
        timeline_ax.set_yticks([])
        
        # Draw timeline events
        if best_path:
            for planet, day, action in best_path:
                timeline_ax.text(day, 0.2, f'{planet}\n({action})', 
                                ha='center', va='bottom', color='green')
            for planet, day in bounty_hunters:
                timeline_ax.text(day, 0.7, f'Hunter@{planet}', 
                                ha='center', va='bottom', color='red', rotation=45)
        
        # Add day markers as circles
        for i in range(empire_data['countdown'] + 1):
            timeline_ax.add_patch(Circle((i, 0.5), 0.1, color='lightgray'))
        
        plt.tight_layout()
        plt.show()
        

    def visualize_mission(self, empire_file: str, odds: float) -> None:
        """Create a visual representation of the mission"""
        # Create figure with extra space at bottom for timeline
        fig = plt.figure(figsize=(15, 12))
        
        # Create main graph axes with space at bottom for timeline
        main_ax = plt.subplot2grid((5, 1), (0, 0), rowspan=4)
        timeline_ax = plt.subplot2grid((5, 1), (4, 0))
        
        # Create graph
        G = nx.Graph()
        
        # Add nodes (planets)
        planet_positions = {
            'Tatooine': (0, 0),
            'Dagobah': (2, 1),
            'Hoth': (4, 1),
            'Endor': (6, 0)
        }
        
        # Add nodes with positions
        for planet, pos in planet_positions.items():
            G.add_node(planet, pos=pos, name=planet)
        
        # Add edges (routes)
        for origin in self.routes:
            for dest, time in self.routes[origin].items():
                G.add_edge(origin, dest, weight=time)
        
        # Load empire data
        with open(empire_file, 'r') as f:
            empire_data = json.load(f)
        
        bounty_hunters = {
            (hunter['planet'], hunter['day']) 
            for hunter in empire_data['bounty_hunters']
        }
        
        # Get the best path
        possible_paths = self._get_possible_paths(empire_data['countdown'])
        best_path = None
        best_probability = 0.0
        
        for path in possible_paths:
            encounters = sum(1 for planet, day, _ in path if (planet, day) in bounty_hunters)
            probability = (0.9 ** encounters) * 100
            if probability > best_probability:
                best_probability = probability
                best_path = path

        # Draw on main axes
        main_ax.set_title(f"Millennium Falcon Mission Map\nSuccess Probability: {odds:.1f}%", pad=20)
        
        pos = nx.get_node_attributes(G, 'pos')
        
        # Draw basic graph structure
        nx.draw_networkx_edges(G, pos, edge_color='gray', width=1, alpha=0.5, ax=main_ax)
        nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, 'weight'))
        nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=1000, ax=main_ax)
        nx.draw_networkx_labels(G, pos)
        
        # Highlight the path
        if best_path:
            path_edges = []
            for i in range(len(best_path)-1):
                current = best_path[i][0]
                next_planet = best_path[i+1][0]
                if (current, next_planet) in G.edges() or (next_planet, current) in G.edges():
                    path_edges.append((current, next_planet))
            
            nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color='green', width=2, ax=main_ax)
            
            # Highlight planets with bounty hunters
            hunter_planets = {planet for planet, day in bounty_hunters}
            nx.draw_networkx_nodes(G, pos, nodelist=hunter_planets, node_color='red', node_size=1000, ax=main_ax)
        
        # Add legend to main graph
        legend_elements = [
            plt.Line2D([0], [0], color='gray', label='Route'),
            plt.Line2D([0], [0], color='green', label='Best Path'),
            plt.scatter([0], [0], c='lightblue', s=100, label='Planet'),
            plt.scatter([0], [0], c='red', s=100, label='Bounty Hunters')
        ]
        main_ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
        
        # Configure timeline axis
        timeline_ax.set_title('Mission Timeline')
        timeline_ax.set_xlim(-0.5, empire_data['countdown'] + 0.5)
        timeline_ax.set_ylim(0, 1)
        timeline_ax.set_xticks(range(empire_data['countdown'] + 1))
        timeline_ax.set_xticklabels([f'Day {i}' for i in range(empire_data['countdown'] + 1)])
        timeline_ax.set_yticks([])
        
        # Draw timeline events
        if best_path:
            # Plot path events
            for planet, day, action in best_path:
                timeline_ax.text(day, 0.2, f'{planet}\n({action})', 
                            ha='center', va='bottom', color='green')
            
            # Plot bounty hunter events
            for planet, day in bounty_hunters:
                timeline_ax.text(day, 0.7, f'Hunter@{planet}', 
                            ha='center', va='bottom', color='red', rotation=45)
        
        # Add day markers
        for i in range(empire_data['countdown'] + 1):
            timeline_ax.add_patch(Circle((i, 0.5), 0.1, color='lightgray'))
        
        # Adjust layout to prevent overlapping
        plt.tight_layout()
        plt.show()




def main_debug():
    print("\n------------------------------------------------------------------\n")
    import argparse
    parser = argparse.ArgumentParser(description="Millennium Faldon; stop the dark star")
    parser.add_argument("falcon", help="Millennium Falcon config")
    parser.add_argument("empire", help="Empire intelloigence data")
    args = parser.parse_args()

    print(f"falcon: {args.falcon}")
    print(f"empire: {args.empire}")
    try:
        # Initialize the Millennium Falcon with the config file
        falcon = MillenniumFalcon(args.falcon)
        
        # Calculate odds and get results
        # Make sure this method returns exactly two values
        odds, debug_info = falcon.calculate_odds_with_debug(args.empire)
        print(debug_info)
        import database_tools as dt
        routes = dt.list_all_routes(Path("data\\universe.db"))
        print(f"Star wars, database of known src->dst routes and their durations (days): {routes}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import sys
    sys.argv = ["millennium_falcon.py", "data\\millennium-falcon.json", "data\\empire041.json"]
    main_debug()
    sys.argv = ["millennium_falcon.py", "data\\millennium-falcon.json", "data\\empire042.json"]
    main_debug()
    sys.argv = ["millennium_falcon.py", "data\\millennium-falcon.json", "data\\empire043.json"]
    main_debug()
    sys.argv = ["millennium_falcon.py", "data\\millennium-falcon.json", "data\\empire044.json"]
    main_debug()
