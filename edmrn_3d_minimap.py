import math
import numpy as np
import tkinter as tk
import customtkinter as ctk
import gc
from typing import Optional, List, Dict, Any, Callable


COLOR_VISITED = '#00FF00'
COLOR_SKIPPED = '#E53935'
COLOR_PENDING = '#ffffff'
COLOR_ROUTE_LINE = '#ff3900'
COLOR_HIGHLIGHT = '#FFFF00'


class MiniMapFrame(ctk.CTkFrame):
    def __init__(self, master, width: int = 480, height: int = 360, 
                 on_system_selected: Optional[Callable] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.width = width
        self.height = height
        self.on_system_selected = on_system_selected
        
        self._update_colors()
        
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            self.fig = Figure(figsize=(6, 4), dpi=100, facecolor=self.bg_color)
            self.ax = self.fig.add_subplot(111, projection='3d', facecolor=self.bg_color)
            
            self.canvas = FigureCanvasTkAgg(self.fig, master=self)
            self.canvas_widget = self.canvas.get_tk_widget()
            self.canvas_widget.pack(fill='both', expand=True, padx=6, pady=6)
            
            self.matplotlib_available = True
        except ImportError:
            self.matplotlib_available = False
            error_label = ctk.CTkLabel(
                self, 
                text="Matplotlib not available\n\nRequired packages:\nmatplotlib\nnumpy", 
                font=("Arial", 12), 
                text_color="orange"
            )
            error_label.pack(padx=20, pady=40)
            self.fig = None
            self.ax = None
            self.canvas = None
        
        if self.matplotlib_available:
            self.route_points: List[Dict[str, Any]] = []
            self._scatter = None
            self._highlight = None
            
            if self.canvas:
                self.cid_scroll = self.canvas.mpl_connect('scroll_event', self._on_scroll)
                self.cid_click = self.canvas.mpl_connect('button_press_event', self._on_click)
            
            self._setup_axes()
            
            if self.ax:
                self.ax.view_init(elev=20., azim=-60)
            
            if self.fig:
                self.fig.tight_layout()
            
            self._error_state = False
    
    def _update_colors(self):
        mode = ctk.get_appearance_mode().lower()
        if mode == 'dark' or mode == 'system':
            self.bg_color = '#212121'
            self.text_color = 'white'
        else:
            self.bg_color = '#FFFFFF'
            self.text_color = 'black'
    
    def _setup_axes(self):
        if not self.matplotlib_available or not self.ax:
            return
        
        try:
            self.ax.set_xlabel('X (LY)', color=self.text_color)
            self.ax.set_ylabel('Y (LY)', color=self.text_color)
            self.ax.set_zlabel('Z (LY)', color=self.text_color)
            
            self.ax.tick_params(colors=self.text_color)
            self.ax.xaxis.label.set_color(self.text_color)
            self.ax.yaxis.label.set_color(self.text_color)
            self.ax.zaxis.label.set_color(self.text_color)
            
            self.ax.xaxis.pane.set_alpha(0.05)
            self.ax.yaxis.pane.set_alpha(0.05)
            self.ax.zaxis.pane.set_alpha(0.05)
            self.ax.grid(color='rgba(200,200,200,0.2)', linestyle=':', linewidth=0.3, alpha=0.2)
        except Exception as e:
            print(f"Axes setup error: {e}")
    
    def _on_scroll(self, event):
        if not self.matplotlib_available or self._error_state:
            return
            
        if event.inaxes != self.ax:
            return
            
        zoom_factor = 1.15 if event.button == 'up' else 0.85
        
        try:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim() 
            zlim = self.ax.get_zlim()
            
            x_center = event.xdata if event.xdata else (xlim[0] + xlim[1]) / 2
            y_center = event.ydata if event.ydata else (ylim[0] + ylim[1]) / 2
            
            new_xlim = [x_center + (x - x_center) * zoom_factor for x in xlim]
            new_ylim = [y_center + (y - y_center) * zoom_factor for y in ylim]
            new_zlim = [(zlim[0] + zlim[1])/2 + (z - (zlim[0] + zlim[1])/2) * zoom_factor for z in zlim]
            
            self.ax.set_xlim(new_xlim)
            self.ax.set_ylim(new_ylim) 
            self.ax.set_zlim(new_zlim)
            
            if self.canvas:
                self.canvas.draw_idle()
            
        except Exception as e:
            print(f"Zoom error: {e}")
            try:
                self.ax.set_xlim([x * zoom_factor for x in self.ax.get_xlim()])
                self.ax.set_ylim([y * zoom_factor for y in self.ax.get_ylim()])
                self.ax.set_zlim([z * zoom_factor for z in self.ax.get_zlim()])
                if self.canvas:
                    self.canvas.draw_idle()
            except Exception:
                pass
    
    def plot_route(self, route_list: List[Dict[str, Any]], show_lines: bool = True, point_size: int = 30) -> bool:
        if not self.matplotlib_available:
            return False
        
        try:
            self._error_state = False
            self.route_points = []
            
            if self._scatter:
                try:
                    self._scatter.remove()
                except Exception:
                    pass
                self._scatter = None
            
            if self._highlight:
                try:
                    self._highlight.remove()
                except Exception:
                    pass
                self._highlight = None
            
            self.ax.cla()
            self._setup_axes()
            
            if not route_list:
                self.ax.text(0.5, 0.5, 0.5, 'No route data', 
                           ha='center', va='center', 
                           color=self.text_color, fontsize=12)
                if self.canvas:
                    self.canvas.draw_idle()
                return True
            
            xs, ys, zs = [], [], []
            colors_list = []
            
            for item in route_list:
                name = item.get('name', 'Unknown')
                coords = item.get('coords')
                status = item.get('status', 'unvisited')
                
                if coords is None or len(coords) < 3:
                    continue
                
                try:
                    x, y, z = float(coords[0]), float(coords[1]), float(coords[2])
                except (ValueError, TypeError):
                    continue
                
                xs.append(x)
                ys.append(y)
                zs.append(z)
                
                if status == 'visited':
                    color = COLOR_VISITED
                elif status == 'skipped':
                    color = COLOR_SKIPPED
                else:
                    color = COLOR_PENDING
                
                colors_list.append(color)
                
                self.route_points.append({
                    'name': name,
                    'coords': (x, y, z),
                    'status': status
                })
            
            if not xs:
                self.ax.text(0.5, 0.5, 0.5, 'No valid coordinates', 
                           ha='center', va='center', 
                           color=self.text_color, fontsize=12)
                if self.canvas:
                    self.canvas.draw_idle()
                return True
            
            self._scatter = self.ax.scatter(
                xs, ys, zs,
                s=point_size,
                c=colors_list,
                marker='o',
                picker=True,
                zorder=5,
                edgecolors='black',
                linewidths=0.5
            )
            
            if show_lines and len(xs) > 1:
                self.ax.plot(
                    xs, ys, zs,
                    c=COLOR_ROUTE_LINE,
                    linewidth=1.0,
                    zorder=1,
                    alpha=0.8
                )
            
            self._adjust_view(xs, ys, zs)
            
            self._create_legend()
            
            if self.canvas:
                self.canvas.draw_idle()
            
            gc.collect()
            return True
            
        except Exception as e:
            print(f"Plot error: {e}")
            self._error_state = True
            
            self.ax.cla()
            self.ax.text(0.5, 0.5, 0.5, f'Error: {str(e)[:50]}', 
                       ha='center', va='center', 
                       color='red', fontsize=10)
            if self.canvas:
                self.canvas.draw_idle()
            return False
    
    def _adjust_view(self, xs: List[float], ys: List[float], zs: List[float]):
        if not self.matplotlib_available:
            return
        
        try:
            max_range = np.array([
                max(xs) - min(xs),
                max(ys) - min(ys), 
                max(zs) - min(zs)
            ]).max() / 2.0
            
            mid_x = (max(xs) + min(xs)) * 0.5
            mid_y = (max(ys) + min(ys)) * 0.5
            mid_z = (max(zs) + min(zs)) * 0.5
            
            self.ax.set_xlim(mid_x - max_range, mid_x + max_range)
            self.ax.set_ylim(mid_y - max_range, mid_y + max_range)
            self.ax.set_zlim(mid_z - max_range, mid_z + max_range)
            
        except Exception as e:
            print(f"View adjustment error: {e}")
            try:
                self.ax.autoscale_view()
            except Exception:
                pass
    
    def _create_legend(self):
        if not self.matplotlib_available:
            return
        
        try:
            from matplotlib.lines import Line2D
            legend_elements = [
                Line2D([0], [0], marker='o', color='w', 
                      label='Visited', markerfacecolor=COLOR_VISITED, markersize=8),
                Line2D([0], [0], marker='o', color='w', 
                      label='Skipped', markerfacecolor=COLOR_SKIPPED, markersize=8),
                Line2D([0], [0], marker='o', color='w', 
                      label='Pending', markerfacecolor=COLOR_PENDING, markersize=8),
            ]
            
            self.ax.legend(
                handles=legend_elements,
                loc='lower center',
                ncols=3,
                facecolor=self.bg_color,
                edgecolor=self.text_color,
                labelcolor=self.text_color,
                fancybox=True,
                shadow=True,
                fontsize='small',
                bbox_to_anchor=(0.5, 0.05)
            )
            
        except Exception as e:
            print(f"Legend creation error: {e}")
    
    def _on_click(self, event):
        if not self.matplotlib_available or event.inaxes != self.ax or event.button != 1 or self._error_state:
            return
            
        if self._scatter is None or not self.route_points:
            return
            
        try:
            points = self._scatter._offsets3d
            xs_3d, ys_3d, zs_3d = points
            
            if len(xs_3d) == 0:
                return
            
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            zlim = self.ax.get_zlim()
            
            nearest_idx = None
            min_distance = float('inf')
            click_threshold = 0.1
            
            for i in range(len(xs_3d)):
                x_3d, y_3d, z_3d = xs_3d[i], ys_3d[i], zs_3d[i]
                
                if not (xlim[0] <= x_3d <= xlim[1] and 
                        ylim[0] <= y_3d <= ylim[1] and 
                        zlim[0] <= z_3d <= zlim[1]):
                    continue
                
                dx = (x_3d - event.xdata) 
                dy = (z_3d - event.ydata) * 0.5
                distance = np.sqrt(dx**2 + dy**2)
                
                if distance < min_distance and distance < click_threshold:
                    min_distance = distance
                    nearest_idx = i
            
            if nearest_idx is not None:
                x_3d, y_3d, z_3d = xs_3d[nearest_idx], ys_3d[nearest_idx], zs_3d[nearest_idx]
                
                for p in self.route_points:
                    if (math.isclose(p['coords'][0], x_3d, abs_tol=0.1) and
                        math.isclose(p['coords'][1], y_3d, abs_tol=0.1) and
                        math.isclose(p['coords'][2], z_3d, abs_tol=0.1)):
                        
                        selected_name = p['name']
                        self.highlight_system(selected_name)
                        
                        if self.on_system_selected:
                            self.on_system_selected(selected_name)
                        return
                        
        except Exception as e:
            print(f"Click handling error: {e}")
    
    def highlight_system(self, name: str) -> bool:
        if not self.matplotlib_available:
            return False
        
        try:
            idx = next((i for i, p in enumerate(self.route_points) if p['name'] == name), None)
            if idx is None:
                return False
            
            x, y, z = self.route_points[idx]['coords']
            
            if self._highlight:
                try:
                    self._highlight.remove()
                except Exception:
                    pass
                self._highlight = None
            
            self._highlight = self.ax.scatter(
                [x], [y], [z],
                s=150,
                edgecolors=COLOR_HIGHLIGHT,
                linewidths=2.0,
                facecolors='none',
                zorder=100
            )
            
            self.ax.set_title(f'Selected: {name}', color=self.text_color, fontsize=10)
            
            if self.canvas:
                self.canvas.draw_idle()
            
            return True
            
        except Exception as e:
            print(f"Highlight error: {e}")
            return False
    
    def clear(self):
        if not self.matplotlib_available:
            return
        
        try:
            if self._scatter:
                try:
                    self._scatter.remove()
                except Exception:
                    pass
                self._scatter = None
            
            if self._highlight:
                try:
                    self._highlight.remove()
                except Exception:
                    pass
                self._highlight = None
            
            self.ax.cla()
            self._setup_axes()
            self.route_points.clear()
            
            if self.canvas:
                self.canvas.draw_idle()
            
            gc.collect()
        except Exception as e:
            print(f"Clear error: {e}")
    
    def refresh_colors(self):
        if not self.matplotlib_available:
            return
        
        try:
            self._update_colors()
            if self.fig:
                self.fig.set_facecolor(self.bg_color)
            if self.ax:
                self.ax.set_facecolor(self.bg_color)
            self._setup_axes()
            
            if self.route_points:
                self.plot_route(self.route_points)
            
            if self.canvas:
                self.canvas.draw_idle()
        except Exception as e:
            print(f"Refresh colors error: {e}")


class MiniMapFrameFallback(ctk.CTkFrame):
    def __init__(self, master, on_system_selected=None, **kwargs):
        super().__init__(master, **kwargs)
        ctk.CTkLabel(
            self, 
            text="3D Map Module Not Available\n\nRequired packages:\nmatplotlib\nnumpy", 
            font=("Arial", 12), 
            text_color="orange"
        ).pack(padx=20, pady=40)
    
    def plot_route(self, *args, **kwargs):
        pass
    
    def highlight_system(self, *args, **kwargs):
        pass
    
    def clear(self):
        pass
    
    def refresh_colors(self):
        pass
