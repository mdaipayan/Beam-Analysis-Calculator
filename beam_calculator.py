import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import cumulative_trapezoid

class BeamAnalyzer:
    def __init__(self, length, beam_type='simply_supported'):
        self.L = length
        self.beam_type = beam_type
        self.loads = []  # List of load dictionaries
        self.supports = []  # Support positions
        self.x = np.linspace(0, length, 1000)
        self.V = np.zeros_like(self.x)  # Shear force
        self.M = np.zeros_like(self.x)  # Bending moment
        
    def add_point_load(self, position, magnitude, direction='down'):
        """Add point load (N or kN)"""
        sign = -1 if direction == 'down' else 1
        self.loads.append({
            'type': 'point',
            'pos': position,
            'mag': sign * magnitude
        })
    
    def add_udl(self, start, end, intensity, direction='down'):
        """Add Uniformly Distributed Load"""
        sign = -1 if direction == 'down' else 1
        self.loads.append({
            'type': 'udl',
            'start': start,
            'end': end,
            'intensity': sign * intensity
        })
    
    def add_moment(self, position, magnitude, direction='clockwise'):
        """Add concentrated moment"""
        sign = -1 if direction == 'clockwise' else 1
        self.loads.append({
            'type': 'moment',
            'pos': position,
            'mag': sign * magnitude
        })
    
    def calculate_reactions(self):
        """Calculate support reactions based on beam type"""
        # Simplified for common cases - extend as needed
        if self.beam_type == 'simply_supported':
            # Sum of moments about left support (x=0)
            total_moment = 0
            total_force = 0
            
            for load in self.loads:
                if load['type'] == 'point':
                    total_moment += load['mag'] * load['pos']
                    total_force += load['mag']
                elif load['type'] == 'udl':
                    length = load['end'] - load['start']
                    force = load['intensity'] * length
                    centroid = (load['start'] + load['end']) / 2
                    total_moment += force * centroid
                    total_force += force
            
            R_right = -total_moment / self.L
            R_left = -total_force - R_right
            
            return [('roller', 0, R_left), ('roller', self.L, R_right)]
            
        elif self.beam_type == 'cantilever':
            # Fixed at x=0, free at x=L
            total_force = 0
            total_moment = 0
            
            for load in self.loads:
                if load['type'] == 'point':
                    total_force += load['mag']
                    total_moment += load['mag'] * load['pos']
                elif load['type'] == 'udl':
                    length = load['end'] - load['start']
                    force = load['intensity'] * length
                    centroid = (load['start'] + load['end']) / 2
                    total_force += force
                    total_moment += force * centroid
            
            return [('fixed', 0, -total_force, -total_moment)]
        
        return []
        
    def plot_beam_setup(self):
        """Generate a diagram of the beam, supports, and loads before analysis"""
        fig, ax = plt.subplots(figsize=(10, 4))
        
        # Draw the beam body
        ax.plot([0, self.L], [0, 0], color='black', linewidth=6, solid_capstyle='butt')
        
        # Add Supports
        reactions = self.calculate_reactions()
        for react in reactions:
            pos = react[1]
            if react[0] == 'roller':
                ax.plot(pos, -0.1, '^', color='green', markersize=15, label='Support')
            elif react[0] == 'fixed':
                ax.axvline(x=pos, ymin=0.4, ymax=0.6, color='red', linewidth=4, label='Fixed End')

        # Add Loads
        for load in self.loads:
            if load['type'] == 'point':
                direction = 1 if load['mag'] > 0 else -1
                ax.annotate('', xy=(load['pos'], 0), xytext=(load['pos'], 0.5 * -direction),
                            arrowprops=dict(facecolor='blue', shrink=0, width=2, headwidth=8))
                ax.text(load['pos'], 0.6 * -direction, f"{abs(load['mag'])}N", ha='center', color='blue')
            
            elif load['type'] == 'udl':
                x_udl = np.linspace(load['start'], load['end'], 10)
                for x_pos in x_udl:
                    ax.annotate('', xy=(x_pos, 0), xytext=(x_pos, 0.3),
                                arrowprops=dict(edgecolor='orange', arrowstyle='->', alpha=0.5))
                ax.plot([load['start'], load['end']], [0.3, 0.3], color='orange', linewidth=2)
                ax.text((load['start'] + load['end'])/2, 0.4, f"{abs(load['intensity'])}N/m", ha='center', color='orange')

        ax.set_ylim(-1, 1)
        ax.set_xlim(-0.1 * self.L, 1.1 * self.L)
        ax.set_title("Beam Loading Setup")
        ax.axis('off')
        plt.tight_layout()
        return fig
    def analyze(self):
        """Perform beam analysis"""
        self.V = np.zeros_like(self.x)
        self.M = np.zeros_like(self.x)
        
        # Add loads to shear force
        for load in self.loads:
            if load['type'] == 'point':
                idx = np.searchsorted(self.x, load['pos'])
                self.V[idx:] += load['mag']
            elif load['type'] == 'udl':
                mask = (self.x >= load['start']) & (self.x <= load['end'])
                self.V[mask] += load['intensity'] * (self.x[mask] - load['start'])
                self.V[self.x > load['end']] += load['intensity'] * (load['end'] - load['start'])
        
        # Calculate reactions and adjust
        reactions = self.calculate_reactions()
        for react in reactions:
            if react[0] in ['roller', 'pin']:
                idx = np.searchsorted(self.x, react[1])
                self.V[idx:] += react[2]
            elif react[0] == 'fixed':
                idx = np.searchsorted(self.x, react[1])
                self.V[idx:] += react[2]
                # Moment reaction affects moment diagram directly
        
        # Calculate bending moment by integrating shear
        self.M = cumulative_trapezoid(self.V, self.x, initial=0)
        
        # Add concentrated moments
        for load in self.loads:
            if load['type'] == 'moment':
                idx = np.searchsorted(self.x, load['pos'])
                self.M[idx:] += load['mag']
        
        # Adjust for cantilever fixed end moment
        if self.beam_type == 'cantilever':
            self.M -= self.M[0]  # Adjust to make moment at fixed end correct
        
        return self.V, self.M
    
    def plot_diagrams(self):
        """Generate matplotlib plots"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        
        # Shear Force Diagram
        ax1.fill_between(self.x, self.V, 0, alpha=0.3, color='blue')
        ax1.plot(self.x, self.V, 'b-', linewidth=2, label='Shear Force')
        ax1.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        ax1.set_ylabel('Shear Force (V)')
        ax1.set_title('Shear Force Diagram (SFD)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Bending Moment Diagram
        ax2.fill_between(self.x, self.M, 0, alpha=0.3, color='red')
        ax2.plot(self.x, self.M, 'r-', linewidth=2, label='Bending Moment')
        ax2.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        ax2.set_ylabel('Bending Moment (M)')
        ax2.set_xlabel('Position along beam (x)')
        ax2.set_title('Bending Moment Diagram (BMD)')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Fixed: Calculate reactions before the loop
        reactions = self.calculate_reactions()
        for react in reactions:
            pos = react[1]
            if react[0] == 'roller':
                ax1.plot(pos, 0, 'go', markersize=10, label='Support')
                ax2.plot(pos, 0, 'go', markersize=10)
            elif react[0] == 'fixed':
                ax1.plot(pos, 0, 'rs', markersize=10, label='Fixed')
                ax2.plot(pos, 0, 'rs', markersize=10)
        
        plt.tight_layout()
        return fig
    
    def get_max_values(self):
        """Return maximum shear and moment values"""
        return {
            'max_shear': np.max(np.abs(self.V)),
            'max_moment': np.max(np.abs(self.M)),
            'max_shear_pos': self.x[np.argmax(np.abs(self.V))],
            'max_moment_pos': self.x[np.argmax(np.abs(self.M))]
        }
