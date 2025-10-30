import pandas as pd
import numpy as np
from python_tsp.heuristics import solve_tsp_local_search 
import math
import glob

SYSTEM_NAME_COLUMN = 'System Name' 
X_COORD_COLUMN = 'X'               
Y_COORD_COLUMN = 'Y'               
Z_COORD_COLUMN = 'Z'

DEFAULT_SHIP_JUMP_RANGE_LY = 70.0 

def calculate_3d_distance_matrix(points_df):
    """ Calculates the 3D space distance (LY) between all waypoints. """
    coords = points_df[[X_COORD_COLUMN, Y_COORD_COLUMN, Z_COORD_COLUMN]].astype(float).values
    N = len(coords)
    distance_matrix = np.zeros((N, N))
    for i in range(N):
        for j in range(i + 1, N):
            dist = np.sqrt(np.sum((coords[i] - coords[j])**2))
            distance_matrix[i, j] = dist
            distance_matrix[j, i] = dist
    return distance_matrix

def calculate_jumps(distances, jump_range):
    """ Calculates the number of jumps required between sequential systems on a route. """
    total_jumps = 0
    for dist in distances:
        total_jumps += math.ceil(dist / jump_range)
    return int(total_jumps)

def find_csv_file():
    """ Searches the current working directory for CSV files and prompts the user for a selection. """
    csv_files = glob.glob('*.csv')

    if not csv_files:
        print("ERROR: No '.csv' files found in the current directory.")
        print("Please ensure your CSV file containing route data is in this folder and try again.")
        return None

    if len(csv_files) == 1:
        selected_file = csv_files[0]
        print(f"-> Auto-Detected: Single CSV file found: '{selected_file}'.")
        return selected_file
    else:
        print("\nMultiple CSV files found. Please enter the number corresponding to the file you want to use:")
        for i, file in enumerate(csv_files):
            print(f"   [{i+1}] {file}")
        
        while True:
            try:
                selection = input("Your Choice (Number): ").strip()
                if not selection:
                     continue

                index = int(selection) - 1
                if 0 <= index < len(csv_files):
                    return csv_files[index]
                else:
                    print("ERROR: Invalid number. Please enter a number from the list.")
            except ValueError:
                print("ERROR: Please enter a valid number.")

def run_tsp_optimizer():
    """ Reads the CSV, calculates distance, optimizes the route, and prompts the user for inputs. """
    
  
    CSV_FILE_PATH = find_csv_file()
    if CSV_FILE_PATH is None:
        return
    
    
    while True:
        try:
            jump_input = input(f"Enter your ship's maximum Jump Range (LY) [Default: {DEFAULT_SHIP_JUMP_RANGE_LY:.1f} LY]: ").strip()
            
            if not jump_input:
                ship_jump_range_ly = DEFAULT_SHIP_JUMP_RANGE_LY
                print(f"-> Using default range ({ship_jump_range_ly:.1f} LY).")
            else:
                ship_jump_range_ly = float(jump_input)
            
            if ship_jump_range_ly <= 0:
                 print("ERROR: Jump range must be a positive number.")
                 continue
            break
        except ValueError:
            print("ERROR: Please enter a valid number (e.g., 70.0 or 81.5).")
            
    
    starting_system_name = input("Enter the name of the system you want to start the route from (Leave empty to find the shortest loop): ").strip()
    
    print(f"Starting: Reading '{CSV_FILE_PATH}' file...")
    try:
        df = pd.read_csv(CSV_FILE_PATH)
        required_columns = [SYSTEM_NAME_COLUMN, X_COORD_COLUMN, Y_COORD_COLUMN, Z_COORD_COLUMN]
        
       
        points = df[required_columns].drop_duplicates(subset=[SYSTEM_NAME_COLUMN]).reset_index(drop=True)
        
       
        try:
             points[X_COORD_COLUMN] = points[X_COORD_COLUMN].astype(float)
             points[Y_COORD_COLUMN] = points[Y_COORD_COLUMN].astype(float)
             points[Z_COORD_COLUMN] = points[Z_COORD_COLUMN].astype(float)
        except ValueError:
             print("\n🚨 CRITICAL ERROR: Could not convert coordinate columns to numbers! Please check your CSV file.")
             return

        N_all = len(points)
        if N_all < 2:
            print("ERROR: At least two unique waypoints are required for routing.")
            return

       
        start_system_data = None
        optimization_points = points
        
        if starting_system_name:
            try:
               
                start_system_data = points[points[SYSTEM_NAME_COLUMN].str.lower() == starting_system_name.lower()].iloc[0]
                
                optimization_points = points[points[SYSTEM_NAME_COLUMN].str.lower() != starting_system_name.lower()].reset_index(drop=True)
                print(f"Starting system fixed: {starting_system_name}")
            except IndexError:
                print(f"WARNING: The desired starting system '{starting_system_name}' was not found in the list. All {N_all} systems will be optimized.")
                starting_system_name = None 

        print(f"🔍 {N_all} unique waypoints found. Ready for optimization.")
        print("-" * 50)
        
        
        distance_matrix_opt = calculate_3d_distance_matrix(optimization_points)
        
        
        print("⚙️ Route optimization starting... (2-Opt Heuristic - For Fast Results)")
        
        permutation_opt, _ = solve_tsp_local_search(distance_matrix_opt, x0=None)
        
        
        optimized_points_opt = optimization_points.iloc[permutation_opt].reset_index(drop=True)
        
       
        if start_system_data is not None:
            optimized_points = pd.concat([start_system_data.to_frame().T, optimized_points_opt], ignore_index=True)
            route_systems = optimized_points[SYSTEM_NAME_COLUMN].tolist()
            
            
            route_distances = []
            for i in range(len(route_systems) - 1):
                p1 = optimized_points.iloc[i]
                p2 = optimized_points.iloc[i+1]
                dist = np.sqrt((p1.X - p2.X)**2 + (p1.Y - p2.Y)**2 + (p1.Z - p2.Z)**2)
                route_distances.append(dist)
        else:
            optimized_points = optimized_points_opt
            route_systems = optimized_points[SYSTEM_NAME_COLUMN].tolist()
            
            
            route_distances = [
                distance_matrix_opt[permutation_opt[i], permutation_opt[i+1]] 
                for i in range(len(permutation_opt) - 1)
            ]

        
        optimized_route_length = sum(route_distances)
        
        total_jumps = calculate_jumps(route_distances, ship_jump_range_ly) 
        
        
        print("\n✅ OPTIMIZATION COMPLETE")
        print("-" * 50)
        print(f"Algorithm: 2-Opt Heuristic")
        print(f"Total Optimized Route Distance (One-Way): {optimized_route_length:.2f} LY")
        print(f"Total Number of Systems to Visit: {len(route_systems)}")
        
        print(f"\n🚀 CMDR Route Details (Explorer Ship):")
        print(f"   Estimated Jumps with Range ({ship_jump_range_ly:.1f} LY): {total_jumps} jumps")
        
        
        print("\nOptimized Route Order (First 15 Systems):")
        for i, system in enumerate(route_systems[:15]): 
            print(f"{i+1}. {system} {'(Start)' if i == 0 and starting_system_name else ''}")
        
        if len(route_systems) > 15:
            print(f"... ({len(route_systems) - 15} more systems - all saved)")
            
        print("-" * 50)
        
        
        output_file_name = f"Optimized_Route_{len(route_systems)}_J{total_jumps}_R{ship_jump_range_ly:.1f}LY.csv"
        optimized_points.to_csv(output_file_name, index=False)
        print(f"✨ Optimized route successfully saved to '{output_file_name}'.")

    except FileNotFoundError:
        print(f"ERROR: The file '{CSV_FILE_PATH}' could not be read. Please ensure your CSV file is not corrupted and is in the correct format.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run_tsp_optimizer()

