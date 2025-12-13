import math
import numpy as np
import tkinter as tk
import customtkinter as ctk
import gc
import matplotlib.pyplot as plt

from edmrn.logger import get_logger

logger = get_logger('MiniMap')

COLOR_VISITED = '#00FF00'
COLOR_SKIPPED = '#ff0000'
COLOR_PENDING = '#ffffff'
COLOR_ROUTE_LINE = '#ed9600'
COLOR_HIGHLIGHT = '#FFFF00'

class MiniMapFrame(ctk.CTkFrame):
    def __init__(self, master, width=480, height=360, on_system_selected=None, **kwargs):
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
            self.route_points = []
            self._scatter = None
            self._highlight = None
            self._lines = None
            
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
            logger.error(f"Axes setup error: {e}")
    
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
            logger.error(f"Zoom error: {e}")
            try:
                self.ax.set_xlim([x * zoom_factor for x in self.ax.get_xlim()])
                self.ax.set_ylim([y * zoom_factor for y in self.ax.get_ylim()])
                self.ax.set_zlim([z * zoom_factor for z in self.ax.get_zlim()])
                if self.canvas:
                    self.canvas.draw_idle()
            except Exception:
                pass
    
    def plot_route(self, route_list, show_lines=True, point_size=30):
        if not self.matplotlib_available:
            return False
        
        try:
            self._error_state = False
            self.route_points = []
            
            if self._scatter is not None and len(route_list) > 0:
                return self._update_scatter_colors(route_list)
            
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
            
            if self._lines:
                try:
                    self._lines.remove()
                except Exception:
                    pass
                self._lines = None
            
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
                    'status': status,
                    'color': color
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
                pickradius=10,
                zorder=5,
                edgecolors='black',
                linewidths=0.5
            )
            
            if show_lines and len(xs) > 1:
                self._lines = self.ax.plot(
                    xs, ys, zs,
                    c=COLOR_ROUTE_LINE,
                    linewidth=1.0,
                    zorder=1,
                    alpha=0.8
                )[0]
            
            self._adjust_view(xs, ys, zs)
            
            self._create_legend()
            
            if self.canvas:
                self.canvas.draw_idle()
            
            gc.collect()
            return True
            
        except Exception as e:
            logger.error(f"Plot error: {e}")
            self._error_state = True
            
            self.ax.cla()
            self.ax.text(0.5, 0.5, 0.5, f'Error: {str(e)[:50]}', 
                       ha='center', va='center', 
                       color='red', fontsize=10)
            if self.canvas:
                self.canvas.draw_idle()
            return False
    
    def _update_scatter_colors(self, route_list):
        if not self.matplotlib_available or not self._scatter:
            return False
        
        try:
            self.route_points = []
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
                    'status': status,
                    'color': color
                })
            
            if not colors_list:
                return False
            
            self._scatter.set_color(colors_list)
            
            if self.canvas:
                self.canvas.draw_idle()
            
            return True
            
        except Exception as e:
            logger.error(f"Update scatter colors error: {e}")
            return False
    
    def update_system_status(self, system_name, status):
        if not self.matplotlib_available or not self._scatter:
            return False
        
        try:
            for point in self.route_points:
                if point['name'] == system_name:
                    if status == 'visited':
                        new_color = COLOR_VISITED
                    elif status == 'skipped':
                        new_color = COLOR_SKIPPED
                    else:
                        new_color = COLOR_PENDING
                    
                    point['status'] = status
                    point['color'] = new_color
                    break
            else:
                return False
            
            route_list = []
            for point in self.route_points:
                route_list.append({
                    'name': point['name'],
                    'coords': point['coords'],
                    'status': point['status']
                })
            
            return self._update_scatter_colors(route_list)
            
        except Exception as e:
            logger.error(f"Update system status error: {e}")
            return False
    
    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        elif len(hex_color) == 3:
            return tuple(int(hex_color[i:i+1] * 2, 16) / 255.0 for i in (0, 1, 2))
        return (1.0, 1.0, 1.0)
    
    def _adjust_view(self, xs, ys, zs):
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
            logger.error(f"View adjustment error: {e}")
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
            logger.error(f"Legend creation error: {e}")
    
    def _on_click(self, event):
        if not self.matplotlib_available or event.inaxes != self.ax or event.button != 1 or self._error_state:
            return
            
        if self._scatter is None or not self.route_points:
            return
            
        try:
            if hasattr(self._scatter, 'contains'):
                contains, ind = self._scatter.contains(event)
            else:
                return
            
            if not contains:
                return
            
            idx = None
            
            if hasattr(ind, 'ind'):
                if len(ind.ind) > 0:
                    idx = ind.ind[0]
            elif isinstance(ind, (list, tuple, np.ndarray)):
                if len(ind) > 0:
                    idx = ind[0] if not isinstance(ind[0], (list, tuple)) else ind[0][0]
            elif isinstance(ind, dict):
                if 'ind' in ind and len(ind['ind']) > 0:
                    idx = ind['ind'][0]
            
            if idx is None:
                return
            
            try:
                idx = int(idx)
            except (ValueError, TypeError):
                return
            
            if idx >= 0 and idx < len(self.route_points):
                selected_point = self.route_points[idx]
                selected_name = selected_point['name']
                
                self.highlight_system(selected_name)
                
                if self.on_system_selected:
                    self.on_system_selected(selected_name)
                        
        except Exception as e:
            logger.error(f"Click handling error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def highlight_system(self, name):
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
            logger.error(f"Highlight error: {e}")
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
            
            if self._lines:
                try:
                    self._lines.remove()
                except Exception:
                    pass
                self._lines = None
            
            self.ax.cla()
            self._setup_axes()
            self.route_points.clear()
            
            if self.canvas:
                self.canvas.draw_idle()
            
            gc.collect()
        except Exception as e:
            logger.error(f"Clear error: {e}")
    
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
            logger.error(f"Refresh colors error: {e}")

    def clear_plot(self):
        if self.ax:
            self.ax.cla()
            self.ax.clear()
        if self.fig:
            self.fig.clf()
        plt.close('all')

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
    
    def update_system_status(self, *args, **kwargs):
        pass
    
    def highlight_system(self, *args, **kwargs):
        pass
    
    def clear(self):
        pass
    
    def refresh_colors(self):
        pass