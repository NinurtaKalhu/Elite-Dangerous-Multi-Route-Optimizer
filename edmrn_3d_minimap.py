import math
import numpy as np
import tkinter as tk
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D

COLOR_VISITED = '#00FF00'
COLOR_SKIPPED = '#E53935'
COLOR_PENDING = '#ffffff'
COLOR_ROUTE_LINE = '#ff3900'
COLOR_JUMP_RANGE = '#808080'

class MiniMapFrame(ctk.CTkFrame):
    
    def _get_mpl_colors(self):
        mode = ctk.get_appearance_mode().lower()
        if mode == 'dark' or mode == 'system':
            return {'face': '#212121', 'text': 'white'} 
        else:
            return {'face': '#FFFFFF', 'text': 'black'}

    def __init__(self, master, width=480, height=360, on_system_selected=None, **kwargs):
        super().__init__(master, **kwargs)
        self.width = width
        self.height = height
        self.on_system_selected = on_system_selected
        colors = self._get_mpl_colors() 
        self.fig = Figure(figsize=(6, 4), dpi=100, facecolor=colors['face'])
        self.ax = self.fig.add_subplot(111, projection='3d', facecolor=colors['face'])
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill='both', expand=True, padx=6, pady=6)
        self.route_points = []
        self._scatter = None
        self._annot = None
        

        self.cid_scroll = self.canvas.mpl_connect('scroll_event', self._on_scroll)
        self.cid_click = self.canvas.mpl_connect('button_press_event', self._on_click)
        

        self.ax.tick_params(colors=colors['text'])
        self.ax.xaxis.label.set_color(colors['text'])
        self.ax.yaxis.label.set_color(colors['text'])
        self.ax.zaxis.label.set_color(colors['text'])
        self.ax.title.set_color(colors['text']) 
        self.ax.set_xlabel('X (LY)')
        self.ax.set_ylabel('Y (LY)')
        self.ax.set_zlabel('Z (LY)')
        self.ax.view_init(elev=20., azim=-60)
        

        self.ax.xaxis.pane.set_alpha(0.05)
        self.ax.yaxis.pane.set_alpha(0.05)
        self.ax.zaxis.pane.set_alpha(0.05)
        self.ax.grid(color='rgba(200,200,200,0.2)', linestyle=':', linewidth=0.3, alpha=0.2)
        
        self.fig.tight_layout()

    def _on_scroll(self, event):
        """Handle mouse scroll for zooming - OPTIMIZED VERSION"""
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
            

            self.canvas.draw_idle()
            
        except Exception as e:

            try:
                self.ax.set_xlim([x * zoom_factor for x in self.ax.get_xlim()])
                self.ax.set_ylim([y * zoom_factor for y in self.ax.get_ylim()])
                self.ax.set_zlim([z * zoom_factor for z in self.ax.get_zlim()])
                self.canvas.draw_idle()
            except Exception:
                pass
        
    def plot_route(self, route_list, show_lines=True, point_size=30):
        """Plot or replot a full route."""
        self.route_points = []
        xs, ys, zs = [], [], []
        colors_list = []
        

        for t in self.fig.texts:
            t.set_visible(False)
        self.fig.texts = []


        for item in route_list:
            name = item.get('name')
            coords = item.get('coords')
            status = item.get('status', 'unvisited')
            if coords is None or len(coords) < 3:
                continue
            x, y, z = float(coords[0]), float(coords[1]), float(coords[2])
            xs.append(x); ys.append(y); zs.append(z)
            
            clr = COLOR_PENDING
            if status == 'visited':
                clr = COLOR_VISITED
            elif status == 'skipped':
                clr = COLOR_SKIPPED
            
            colors_list.append(clr)
            
            self.route_points.append({'name': name, 'coords': (x, y, z), 'status': status})
        

        self.ax.cla()
        colors = self._get_mpl_colors()
        text_color = colors['text']
        mpl_color = colors['face']
        self.ax.set_facecolor(mpl_color)
        self.fig.set_facecolor(mpl_color)
        self.ax.tick_params(colors=text_color)
        self.ax.set_xlabel('X (LY)', color=text_color)
        self.ax.set_ylabel('Y (LY)', color=text_color)
        self.ax.set_zlabel('Z (LY)', color=text_color)
        self.ax.xaxis.pane.set_alpha(0.05)
        self.ax.yaxis.pane.set_alpha(0.05)
        self.ax.zaxis.pane.set_alpha(0.05)
        self.ax.grid(color='rgba(200,200,200,0.2)', linestyle=':', linewidth=0.3, alpha=0.2)
        

        if xs:
            self._scatter = self.ax.scatter(xs, ys, zs, 
                                            s=point_size, 
                                            c=colors_list, 
                                            marker='o', 
                                            picker=True, 
                                            zorder=5)
            

            if show_lines and len(xs) > 1:
                self.ax.plot(xs, ys, zs, c=COLOR_ROUTE_LINE, linewidth=1.0, zorder=1, alpha=0.8)
            

            max_range = np.array([max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs)]).max() / 2.0
        
            mid_x = (max(xs)+min(xs)) * 0.5
            mid_y = (max(ys)+min(ys)) * 0.5
            mid_z = (max(zs)+min(zs)) * 0.5
            
            self.ax.set_xlim(mid_x - max_range, mid_x + max_range)
            self.ax.set_ylim(mid_y - max_range, mid_y + max_range)
            self.ax.set_zlim(mid_z - max_range, mid_z + max_range)
            

            visited_handle = self.ax.scatter([], [], [], color=COLOR_VISITED, s=point_size, label='Visited')
            skipped_handle = self.ax.scatter([], [], [], color=COLOR_SKIPPED, s=point_size, label='Skipped')
            pending_handle = self.ax.scatter([], [], [], color=COLOR_PENDING, s=point_size, label='Pending')

            self.fig.legend(handles=[visited_handle, skipped_handle, pending_handle], 
                            loc='lower center', 
                            ncols=3, 
                            facecolor=mpl_color, 
                            edgecolor=text_color,
                            labelcolor=text_color,
                            fancybox=True, 
                            shadow=True, 
                            fontsize='small',
                            bbox_to_anchor=(0.5, 0.05))

        self.canvas.draw_idle()

    def _on_click(self, event):
        """Handle click event to select the nearest star - OPTIMIZED VERSION"""

        if event.inaxes != self.ax or event.button != 1:
            return
            
        if self._scatter is None or len(self.route_points) == 0:
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

            pass

    def highlight_system(self, name):
        """Highlights the system on the map, centers the view, and re-plots."""
        idx = next((i for i, p in enumerate(self.route_points) if p['name'] == name), None)
        if idx is None:
            return
            
        x, y, z = self.route_points[idx]['coords']
        

        self.plot_route(self.route_points, point_size=30) 
        

        try:
            self.ax.scatter([x], [y], [z], s=150, edgecolors='yellow', linewidths=2.0, facecolors='none', zorder=100)            
            self.canvas.draw_idle()
        except Exception:
            pass

    def _center_on_point(self, x, y, z):
        """Center the view on a specific point"""
        span = 20.0 
        self.ax.set_xlim(x - span, x + span)
        self.ax.set_ylim(y - span, y + span)
        self.ax.set_zlim(z - span, z + span)

if __name__ == '__main__':
    import random
    root = tk.Tk()
    root.geometry('700x520')
    root.title("3D Map Test")
    test_route = []
    statuses = ['visited', 'skipped', 'unvisited']
    for i in range(20):
        status = random.choice(statuses)
        test_route.append({
            'name': f"Star {i}",
            'coords': (random.uniform(-100, 100), random.uniform(-100, 100), random.uniform(-100, 100)),
            'status': status
        })

    def handle_selection(name):
        print(f"Selected System: {name}")

    map_frame = MiniMapFrame(root, on_system_selected=handle_selection)
    map_frame.pack(fill='both', expand=True, padx=20, pady=20)
    map_frame.plot_route(test_route)
    map_frame.highlight_system(test_route[5]['name'])
    
    root.mainloop()
