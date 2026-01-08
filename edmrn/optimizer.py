import math
import numpy as np
import pandas as pd
import json
from scipy.spatial.distance import cdist
from python_tsp.heuristics import solve_tsp_lin_kernighan
from tqdm import tqdm
import time
import multiprocessing
import threading
from typing import Callable
def _tsp_solve_wrapper(distance_matrix):
    return solve_tsp_lin_kernighan(distance_matrix, x0=None)
def _tsp_proc_worker(distance_matrix, q):
    try:
        result = _tsp_solve_wrapper(distance_matrix)
        q.put(result)
    except Exception as e:
        q.put(('__ERROR__', str(e)))
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from edmrn.logger import get_logger
from edmrn.utils import atomic_write_json
logger = get_logger('Optimizer')
SYSTEM_NAME_COLUMN = 'System Name'
X_COORD_COLUMN = 'X'
Y_COORD_COLUMN = 'Y'
Z_COORD_COLUMN = 'Z'
STATUS_VISITED = 'visited'
STATUS_SKIPPED = 'skipped'
STATUS_UNVISITED = 'unvisited'
class RouteOptimizer:
    def __init__(self):
        self.system_name_column = SYSTEM_NAME_COLUMN
        self.x_column = X_COORD_COLUMN
        self.y_column = Y_COORD_COLUMN
        self.z_column = Z_COORD_COLUMN
        self._cache = {}
        self._performance_stats = {
            'distance_matrix_time': 0,
            'tsp_time': 0,
            'processing_time': 0
        }
    def _get_performance_stats(self) -> Dict:
        return self._performance_stats.copy()
    def _reset_performance_stats(self):
        self._performance_stats = {
            'distance_matrix_time': 0,
            'tsp_time': 0,
            'processing_time': 0
        }
    def calculate_distance_matrix(self, coords: np.ndarray, method: str = 'auto', progress_callback: Callable[[str, float], None] = None, cancel_event: threading.Event = None) -> np.ndarray:
        n = len(coords)
        logger.info(f"Calculating distance matrix for {n} points...")
        start_time = time.time()
        try:
            if method == 'auto':
                if n <= 2000:
                    result = self._distance_matrix_scipy(coords)
                elif n <= 10000:
                    result = self._distance_matrix_vectorized_optimized(coords)
                else:
                    result = self._distance_matrix_chunked_optimized(coords, progress_callback=progress_callback, cancel_event=cancel_event)
            elif method == 'scipy':
                result = self._distance_matrix_scipy(coords)
            elif method == 'vectorized':
                result = self._distance_matrix_vectorized_optimized(coords)
            elif method == 'chunked':
                result = self._distance_matrix_chunked_optimized(coords, progress_callback=progress_callback, cancel_event=cancel_event)
            else:
                raise ValueError(f"Unknown method: {method}")
            elapsed = time.time() - start_time
            self._performance_stats['distance_matrix_time'] = elapsed
            logger.info(f"Distance matrix calculated in {elapsed:.2f} seconds")
            return result
        except Exception as e:
            logger.error(f"Error calculating distance matrix: {e}")
            if isinstance(e, RuntimeError) and str(e).startswith('Optimization cancelled'):
                raise
            return self._distance_matrix_simple(coords)
    def _distance_matrix_scipy(self, coords: np.ndarray) -> np.ndarray:
        try:
            return cdist(coords, coords, metric='euclidean').astype(np.float32)
        except ImportError:
            logger.warning("SciPy not available, falling back to vectorized method")
            return self._distance_matrix_vectorized_optimized(coords)
    def _distance_matrix_vectorized_optimized(self, coords: np.ndarray) -> np.ndarray:
        n = coords.shape[0]
        required_memory_gb = (n * n * 4) / (1024 ** 3)
        if required_memory_gb > 2.0:
            logger.warning(f"Vectorized method would use ~{required_memory_gb:.2f} GB RAM, falling back to chunked method")
            return self._distance_matrix_chunked_optimized(coords)
        x = coords[:, 0:1]
        y = coords[:, 1:2]
        z = coords[:, 2:3]
        dx = x - x.T
        dy = y - y.T
        dz = z - z.T
        dist_sq = dx * dx
        dist_sq += dy * dy
        dist_sq += dz * dz
        dist = np.sqrt(dist_sq, out=dist_sq)
        np.fill_diagonal(dist, 0.0)
        return dist.astype(np.float32)
    def _distance_matrix_chunked_optimized(self, coords: np.ndarray, chunk_size: int = None, progress_callback: Callable[[str, float], None] = None, cancel_event: threading.Event = None) -> np.ndarray:
        n = coords.shape[0]
        if chunk_size is None:
            target_memory_mb = 250
            chunk_size = int(np.sqrt((target_memory_mb * 1024 * 1024) / (4 * 4)))
            chunk_size = max(100, min(800, chunk_size))
        logger.info(f"Using chunked calculation with chunk_size={chunk_size}")
        dist = np.zeros((n, n), dtype=np.float32)
        total_blocks = ((n + chunk_size - 1) // chunk_size)
        total_blocks = total_blocks * (total_blocks + 1) // 2
        blocks_done = 0
        with tqdm(total=total_blocks, desc="Distance Matrix", unit="block", leave=False) as pbar:
            for i in range(0, n, chunk_size):
                i_end = min(i + chunk_size, n)
                chunk_i = coords[i:i_end]
                for j in range(i, n, chunk_size):
                    if cancel_event and cancel_event.is_set():
                        logger.info("Distance matrix calculation cancelled by user")
                        raise RuntimeError("Optimization cancelled by user during distance matrix calculation")
                    j_end = min(j + chunk_size, n)
                    chunk_j = coords[j:j_end]
                    diff = chunk_i[:, np.newaxis, :] - chunk_j[np.newaxis, :, :]
                    block_dist = np.sqrt(np.einsum('ijk,ijk->ij', diff, diff))
                    dist[i:i_end, j:j_end] = block_dist
                    if i != j:
                        dist[j:j_end, i:i_end] = block_dist.T
                    blocks_done += 1
                    pbar.update(1)
                    if progress_callback:
                        try:
                            progress_callback('distance_matrix', blocks_done / total_blocks)
                        except Exception:
                            pass
        np.fill_diagonal(dist, 0.0)
        return dist
    def _distance_matrix_simple(self, coords: np.ndarray, progress_callback: Callable[[str, float], None] = None, cancel_event: threading.Event = None) -> np.ndarray:
        n = coords.shape[0]
        dist = np.zeros((n, n), dtype=np.float32)
        logger.info("Using simple distance calculation (fallback)")
        total = n
        done = 0
        for i in tqdm(range(n), desc="Calculating distances", leave=False):
            if cancel_event and cancel_event.is_set():
                logger.info("Simple distance calculation cancelled by user")
                raise RuntimeError("Optimization cancelled by user during distance calculation")
            for j in range(i + 1, n):
                dx = coords[i, 0] - coords[j, 0]
                dy = coords[i, 1] - coords[j, 1]
                dz = coords[i, 2] - coords[j, 2]
                distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                dist[i, j] = distance
                dist[j, i] = distance
            done += 1
            if progress_callback:
                try:
                    progress_callback('distance_matrix', done / total)
                except Exception:
                    pass
        return dist
    def _nearest_neighbor_tsp(self, distance_matrix: np.ndarray) -> List[int]:
        n = distance_matrix.shape[0]
        if n == 0:
            return []
        visited = [False] * n
        tour = [0]
        visited[0] = True
        for _ in range(1, n):
            last = tour[-1]
            dists = distance_matrix[last]
            next_idx = None
            min_d = float('inf')
            for i in range(n):
                if not visited[i] and dists[i] < min_d:
                    min_d = dists[i]
                    next_idx = i
            if next_idx is None:
                for i in range(n):
                    if not visited[i]:
                        next_idx = i
                        break
            visited[next_idx] = True
            tour.append(next_idx)
        return tour
    def _solve_tsp_with_timeout(self, distance_matrix: np.ndarray, timeout: float = None) -> Tuple[List[int], float]:
        if timeout is None:
            timeout = getattr(self, 'tsp_timeout_seconds', 30)
        start = time.time()
        try:
            ctx = multiprocessing.get_context('spawn')
            q = ctx.Queue()
            p = ctx.Process(target=_tsp_proc_worker, args=(distance_matrix, q))
            p.start()
            p.join(timeout)
            if p.is_alive():
                logger.warning(f"TSP solver timed out after {timeout}s; terminating worker and falling back to nearest-neighbor heuristic")
                p.terminate()
                p.join()
                start2 = time.time()
                permutation = self._nearest_neighbor_tsp(distance_matrix)
                return permutation, time.time() - start2
            try:
                result = q.get_nowait()
            except Exception:
                logger.error("TSP worker finished but returned no data; falling back to nearest-neighbor heuristic")
                return self._nearest_neighbor_tsp(distance_matrix), time.time() - start
            if isinstance(result, tuple):
                permutation = result[0]
            else:
                permutation = result
            elapsed = time.time() - start
            return permutation, elapsed
        except Exception as e:
            logger.error(f"TSP solver error: {e}; falling back to nearest-neighbor heuristic")
            start2 = time.time()
            permutation = self._nearest_neighbor_tsp(distance_matrix)
            return permutation, time.time() - start2
    def calculate_jumps(self, distances: np.ndarray, jump_range: float) -> int:
        if len(distances) == 0:
            return 0
        if jump_range <= 0:
            raise ValueError(f"Jump range must be positive, got {jump_range}")
        jumps_per_segment = np.ceil(distances / jump_range)
        total_jumps = int(np.sum(jumps_per_segment))
        return total_jumps
    def check_csv_columns(self, file_path: str) -> Tuple[Dict[str, bool], List[str]]:
        try:
            df = pd.read_csv(file_path, nrows=1)
            columns_status = {
                'System Name': self.system_name_column in df.columns,
                'Body Name': any(col in df.columns for col in ['Body Name', 'Name', 'BodyName', 'body_name']),
                'X Coord': self.x_column in df.columns,
                'Y Coord': self.y_column in df.columns,
                'Z Coord': self.z_column in df.columns
            }
            return columns_status, df.columns.tolist()
        except Exception as e:
            logger.error(f"CSV column check error: {e}")
            return None, []
    def group_systems_and_bodies(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.system_name_column not in df.columns:
            raise ValueError("CSV must contain a 'System Name' column for grouping.")
        body_columns = ['Body Name', 'Name', 'BodyName', 'body_name']
        body_column = next((col for col in body_columns if col in df.columns), None)
        agg_dict = {
            self.x_column: 'first',
            self.y_column: 'first',
            self.z_column: 'first'
        }
        if body_column:
            agg_dict[body_column] = lambda x: [str(i) for i in x if pd.notna(i)]
        else:
            logger.warning("No body name column found in CSV")
        grouped_df = df.groupby(self.system_name_column, sort=False, as_index=False).agg(agg_dict)
        if body_column:
            grouped_df['Body_Names'] = grouped_df[body_column]
            grouped_df['Body_Count'] = grouped_df['Body_Names'].apply(len)
            grouped_df = grouped_df.drop(columns=[body_column])
        else:
            grouped_df['Body_Names'] = [[] for _ in range(len(grouped_df))]
            grouped_df['Body_Count'] = 0
        logger.info(f"Systems grouped. Total unique systems: {len(grouped_df)}")
        return grouped_df
    def optimize_route(self, csv_path: str, jump_range: float,
                      starting_system_name: str = '',
                      existing_status: Dict[str, str] = None,
                      progress_callback: Callable[[str, float], None] = None,
                      cancel_event: threading.Event = None) -> Dict[str, Any]:
        self._reset_performance_stats()
        total_start_time = time.time()
        try:
            if existing_status is None:
                existing_status = {}
            if jump_range <= 0:
                raise ValueError(f"Jump range must be positive, got {jump_range}")
            logger.info(f"Loading CSV: {csv_path}")
            df = pd.read_csv(csv_path)
            logger.info(f"CSV loaded: {len(df)} rows, columns: {df.columns.tolist()}")
            start_time = time.perf_counter()
            required_cols = {self.system_name_column, self.x_column, self.y_column, self.z_column}
            if not required_cols.issubset(set(df.columns)):
                missing = required_cols - set(df.columns)
                raise ValueError(f"CSV missing required columns: {', '.join(missing)}")
            df_grouped = self.group_systems_and_bodies(df)
            logger.info(f"Grouping done: {len(df_grouped)} unique systems")
            points = df_grouped[[self.system_name_column, self.x_column, self.y_column, self.z_column]].copy()
            n_all = len(points)
            recommended = self.get_recommended_method(n_all)
            logger.info(f"Recommended distance matrix method for {n_all} points: {recommended}")
            if n_all < 2:
                raise ValueError("At least two unique waypoints are required for routing.")
            start_system_data = None
            optimization_points = points.copy()
            original_starting_system_name = starting_system_name
            if starting_system_name:
                starting_system_name_clean = starting_system_name.lower().strip()
                mask = optimization_points[self.system_name_column].str.lower().str.strip() == starting_system_name_clean
                matching_systems = optimization_points[mask]
                if len(matching_systems) > 0:
                    start_system_data = matching_systems.iloc[0]
                    optimization_points = optimization_points[~mask].reset_index(drop=True)
                    logger.info(f"Starting system '{starting_system_name}' found and set as route start")
                else:
                    logger.warning(f"Starting system '{starting_system_name}' not found in CSV. Using auto-optimized start.")
            if len(optimization_points) == 0:
                raise ValueError("No systems left to optimize after removing starting system.")
            coords_array = optimization_points[[self.x_column, self.y_column, self.z_column]].astype(np.float64).values
            distance_matrix_opt = self.calculate_distance_matrix(coords_array, method='auto', progress_callback=progress_callback, cancel_event=cancel_event)
            logger.info(f"Distance matrix shape: {distance_matrix_opt.shape}; time since start: {time.perf_counter() - start_time:.2f}s")
            if progress_callback:
                try:
                    progress_callback('distance_matrix_done', 1.0)
                except Exception:
                    pass
            if cancel_event and cancel_event.is_set():
                raise RuntimeError('Optimization cancelled by user before TSP')
            distance_matrix_opt = distance_matrix_opt.astype(np.float64)
            logger.debug(f"Converted distance matrix to float64 for TSP solver (shape {distance_matrix_opt.shape})")
            if len(distance_matrix_opt) > 1:
                if progress_callback:
                    try:
                        progress_callback('tsp_start', None)
                    except Exception:
                        pass
                logger.info(f"Starting TSP solver for {len(distance_matrix_opt)} nodes (timeout {getattr(self, 'tsp_timeout_seconds', 30)}s)")
                permutation_opt, tsp_elapsed = self._solve_tsp_with_timeout(distance_matrix_opt)
                optimized_names = optimization_points.iloc[permutation_opt][self.system_name_column].tolist()
                self._performance_stats['tsp_time'] = tsp_elapsed
                logger.info(f"TSP solver completed in {tsp_elapsed:.2f}s")
                if progress_callback:
                    try:
                        progress_callback('tsp_done', 1.0)
                    except Exception:
                        pass
            else:
                optimized_names = optimization_points[self.system_name_column].tolist()
                self._performance_stats['tsp_time'] = 0.0
            if start_system_data is not None:
                optimized_names.insert(0, start_system_data[self.system_name_column])
            optimized_points_full = df[df[self.system_name_column].isin(optimized_names)]
            system_bodies = df.groupby(self.system_name_column)['Name'].apply(list).to_dict()
            optimized_points_full = optimized_points_full.drop_duplicates(self.system_name_column).copy()
            optimized_points_full['Body_Names'] = optimized_points_full[self.system_name_column].map(
                lambda x: system_bodies.get(x, [])
            )
            try:
                name_to_index = {name: idx for idx, name in enumerate(optimized_names)}
                optimized_points_full['order'] = optimized_points_full[self.system_name_column].map(name_to_index)
                optimized_points_full = optimized_points_full.sort_values('order').drop(columns=['order'])
            except KeyError as e:
                missing_systems = [name for name in optimized_names if name not in optimized_points_full.index]
                logger.warning(f"Some systems not found during reordering: {missing_systems}")
                found_names = [name for name in optimized_names if name in optimized_points_full.index]
                optimized_points_full = optimized_points_full.set_index(self.system_name_column).loc[found_names].reset_index()
                optimized_names = found_names
            if len(optimized_points_full) > 1:
                coords_values = optimized_points_full[[self.x_column, self.y_column, self.z_column]].values
                route_distances = np.sqrt(
                    np.sum(np.diff(coords_values, axis=0) ** 2, axis=1)
                ).tolist()
            else:
                route_distances = []
            optimized_route_length = float(np.sum(route_distances)) if route_distances else 0.0
            total_jumps = self.calculate_jumps(np.array(route_distances), jump_range)
            optimized_points_full['Status'] = optimized_points_full[self.system_name_column].map(
                lambda x: existing_status.get(x, STATUS_UNVISITED)
            )
            route_data = []
            records = optimized_points_full.to_dict('records')
            for rec in records:
                coords = [
                    float(rec.get(self.x_column, 0) or 0),
                    float(rec.get(self.y_column, 0) or 0),
                    float(rec.get(self.z_column, 0) or 0)
                ]
                bodies = rec.get('Body_Names', [])
                if not isinstance(bodies, list):
                    bodies = []
                route_data.append({
                    'name': rec[self.system_name_column],
                    'status': rec['Status'],
                    'coords': coords,
                    'bodies_to_scan': bodies,
                    'body_count': int(rec.get('Body_Count', 0))
                })
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_folder_name = f"Route_{len(optimized_names)}_sys_{timestamp}"
            from edmrn.config import Paths
            backup_folder_path = Path(Paths.get_backup_folder()) / backup_folder_name
            backup_folder_path.mkdir(parents=True, exist_ok=True)
            csv_filename = "optimized_route.csv"
            csv_path_backup = backup_folder_path / csv_filename
            optimized_points_full.to_csv(csv_path_backup, index=False)
            logger.info(f"Optimized CSV backed up to {csv_path_backup}; time since start: {time.perf_counter() - start_time:.2f}s")
            status_data = []
            for _, row in optimized_points_full.iterrows():
                system_name = row[self.system_name_column]
                current_status = existing_status.get(system_name, STATUS_UNVISITED) if existing_status else STATUS_UNVISITED
                status_data.append({
                    'name': system_name,
                    'status': current_status
                })
            status_path = backup_folder_path / "route_status.json"
            with open(status_path, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Route status saved to {status_path}; time since start: {time.perf_counter() - start_time:.2f}s")
            logger.info(f"Route saved to backup folder: {backup_folder_name}")
            total_time = time.time() - total_start_time
            self._performance_stats['processing_time'] = total_time
            logger.info(f"Optimization completed in {total_time:.2f} seconds")
            logger.info(f" - Distance matrix: {self._performance_stats['distance_matrix_time']:.2f}s")
            logger.info(f" - TSP: {self._performance_stats['tsp_time']:.2f}s")
            logger.info(f" - Total: {total_time:.2f}s")
            return {
                'success': True,
                'route_data': route_data,
                'optimized_df': optimized_points_full,
                'total_distance': optimized_route_length,
                'total_jumps': total_jumps,
                'num_systems': len(optimized_names),
                'starting_system': original_starting_system_name if original_starting_system_name else 'Auto',
                'backup_folder': str(backup_folder_path),
                'backup_name': backup_folder_name,
                'performance_stats': self._performance_stats.copy()
            }
        except ValueError as e:
            raise
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e),
                'route_data': [],
                'optimized_df': None,
                'total_distance': 0,
                'total_jumps': 0,
                'num_systems': 0,
                'performance_stats': self._performance_stats.copy()
            }
    def estimate_memory_usage(self, n_points: int, dtype: str = 'float32') -> float:
        bytes_per_element = 4 if dtype == 'float32' else 8
        total_elements = n_points * n_points
        memory_bytes = total_elements * bytes_per_element
        return memory_bytes / (1024 * 1024)
    def get_recommended_method(self, n_points: int) -> str:
        memory_mb = self.estimate_memory_usage(n_points)
        if n_points <= 2000:
            return 'scipy'
        elif memory_mb <= 2000:
            return 'vectorized'
        else:
            return 'chunked'
    def validate_coordinates(self, coords: np.ndarray) -> bool:
        if not isinstance(coords, np.ndarray):
            return False
        if len(coords.shape) != 2 or coords.shape[1] != 3:
            return False
        if np.any(np.isnan(coords)) or np.any(np.isinf(coords)):
            return False
        return True
def quick_optimize(csv_path: str, jump_range: float = 70.0,
                   starting_system: str = '', method: str = 'auto') -> Dict[str, Any]:
    optimizer = RouteOptimizer()
    return optimizer.optimize_route(csv_path, jump_range, starting_system)
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        print(f"Testing optimizer with: {csv_file}")
        optimizer = RouteOptimizer()
        result = optimizer.optimize_route(csv_file, jump_range=70.0)
        if result['success']:
            print(f"✓ Optimization successful!")
            print(f" Systems: {result['num_systems']}")
            print(f" Distance: {result['total_distance']:.2f} LY")
            print(f" Jumps: {result['total_jumps']}")
            print(f" Output: {result['output_file']}")
        else:
            print(f"✗ Optimization failed: {result['error']}")
    else:
        print("Usage: python optimizer.py <csv_file>")
