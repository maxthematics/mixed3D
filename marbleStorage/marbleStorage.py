## kullerbue-marble-storage
import cadquery as cq

# =============================================================================
# PARAMETERS
# =============================================================================

# Marble dimensions
marble_radius = 46 / 2      # mm (Kullerbü marble diameter / 2)
clearance = 2               # mm extra space around marble

# Layout
marbles_per_layer = 2       # marbles on first layer (upper layers have one less)
slope = 0.03                # height gain per mm length

# Turn geometry
turn_factor = 1.3           # turn_radius = tube_radius * turn_factor

# Outlet
outlet_factor = 1.3         # outlet_length = tube_radius * outlet_factor

# Housing
wall_thickness = 5          # mm
enable_fillet = True        # round edges
fillet_radius = 4           # mm

# Windows
enable_windows = True
window_height_factor = 0.8  # Höhe = tube_radius * factor
window_margin_factor = 0.5  # Abstand vom Rand = tube_radius * factor

# =============================================================================
# DERIVED VALUES
# =============================================================================

tube_radius = marble_radius + clearance
turn_radius = tube_radius * turn_factor
outlet_length = tube_radius * outlet_factor

# =============================================================================
# PATH GENERATION
# =============================================================================

def make_marble_path():
    """Generate the serpentine path for the marble tunnel."""
    
    # Section lengths
    layer1_len = marbles_per_layer * tube_radius * 2
    layer2_len = (marbles_per_layer - 1) * tube_radius * 2
    layer3_len = (marbles_per_layer - 1) * tube_radius * 2 + tube_radius
    
    # Height gains
    layer1_height = layer1_len * slope
    layer2_height = layer2_len * slope
    layer3_height = layer3_len * slope
    
    # Outlet
    outlet_start_y = 0
    outlet_start_z = 0
    outlet_end_y = outlet_length
    outlet_end_z = 0
    
    # Layer 1 (direction: +Y)
    layer1_start_y = outlet_end_y
    layer1_start_z = outlet_end_z
    layer1_end_y = outlet_end_y + layer1_len
    layer1_end_z = layer1_height
    
    # Turn 1
    turn1_apex_y = layer1_end_y + turn_radius
    turn1_apex_z = layer1_end_z + turn_radius
    
    # Layer 2 (direction: -Y)
    layer2_start_y = layer1_end_y
    layer2_start_z = layer1_end_z + turn_radius * 2
    layer2_end_y = layer2_start_y - layer2_len
    layer2_end_z = layer2_start_z + layer2_height
    
    # Turn 2
    turn2_apex_y = layer2_end_y - turn_radius
    turn2_apex_z = layer2_end_z + turn_radius
    
    # Layer 3 (direction: +Y)
    layer3_start_y = layer2_end_y
    layer3_start_z = layer2_end_z + turn_radius * 2
    layer3_end_y = layer3_start_y + layer3_len
    layer3_end_z = layer3_start_z + layer3_height
    
    # Arcs with tangents
    turn1 = cq.Edge.makeSpline(
        [cq.Vector(0, layer1_end_y, layer1_end_z),
         cq.Vector(0, turn1_apex_y, turn1_apex_z),
         cq.Vector(0, layer2_start_y, layer2_start_z)],
        tangents=[cq.Vector(0, 1, slope), cq.Vector(0, 0, 1), cq.Vector(0, -1, slope)]
    )
    
    turn2 = cq.Edge.makeSpline(
        [cq.Vector(0, layer2_end_y, layer2_end_z),
         cq.Vector(0, turn2_apex_y, turn2_apex_z),
         cq.Vector(0, layer3_start_y, layer3_start_z)],
        tangents=[cq.Vector(0, -1, slope), cq.Vector(0, 0, 1), cq.Vector(0, 1, slope)]
    )
    
    # Assemble edges
    edges = [
        cq.Edge.makeLine((0, outlet_start_y, outlet_start_z), (0, outlet_end_y, outlet_end_z)),
        cq.Edge.makeLine((0, layer1_start_y, layer1_start_z), (0, layer1_end_y, layer1_end_z)),
        turn1,
        cq.Edge.makeLine((0, layer2_start_y, layer2_start_z), (0, layer2_end_y, layer2_end_z)),
        turn2,
        cq.Edge.makeLine((0, layer3_start_y, layer3_start_z), (0, layer3_end_y, layer3_end_z)),
    ]
    
    return cq.Wire.assembleEdges(edges)

# =============================================================================
# GROOVE SOLID
# =============================================================================

def make_groove_solid(path):
    """Create the tube solid by sweeping a circle along the path."""
    
    profile = cq.Workplane("XZ").circle(tube_radius)
    tube = profile.sweep(path, isFrenet=True, transition="round")
    tube = tube.clean()
    
    sphere_start = cq.Workplane("XY").sphere(tube_radius).translate((0, 0, -.35 * tube_radius))
    sphere_end = cq.Workplane("XY").sphere(tube_radius).translate(path.endPoint().toTuple())
    
    return tube.union(sphere_start).union(sphere_end)

# =============================================================================
# WINDOWS
# =============================================================================

def make_windows():
    """Create window cutouts on the long sides of the box."""
    
    layer1_len = marbles_per_layer * tube_radius * 2
    layer2_len = (marbles_per_layer - 1) * tube_radius * 2
    layer3_len = (marbles_per_layer - 1) * tube_radius * 2 + tube_radius
    
    layer1_height = layer1_len * slope
    layer2_height = layer2_len * slope
    layer3_height = layer3_len * slope
    
    # Gesamthöhe der Röhre
    total_height = layer1_height + turn_radius * 2 + layer2_height + turn_radius * 2 + layer3_height
    
    # Box-Länge (Y-Richtung)
    box_start_y = outlet_length
    box_end_y = outlet_length + layer1_len + turn_radius
    box_length = box_end_y - box_start_y
    
    window_length = box_length * 0.8
    window_height = tube_radius * window_height_factor
    window_depth = tube_radius * 3
    
    # Mitte der Box (Y-Richtung)
    window_center_y = box_start_y + box_length / 2
    
    # Oberes Fenster - bei 2/3 der Höhe
    window_upper_z = total_height * 5/10
    
    window_upper = (
        cq.Workplane("XY")
        .transformed(offset=(0, window_center_y, window_upper_z))
        .box(window_depth, window_length, window_height)
        .edges("|Y").fillet(window_height / 2 - 0.1)
    )
    
    # Unteres Fenster - auf Höhe von Layer 1
    window_lower_z = layer1_height / 2
    
    window_lower = (
        cq.Workplane("XY")
        .transformed(offset=(0, window_center_y, window_lower_z))
        .box(window_depth, window_length, window_height)
        .edges("|Y").fillet(window_height / 2 - 0.1)
    )

    # Rundes Fenster vorne - Höhe der unteren Kurve (Turn 2)
    turn2_z = layer1_height + turn_radius * 2 + layer2_height + 0.8 * turn_radius

    window_front = (
        cq.Workplane("XZ")
        .workplane(offset=outlet_length)  # Y-Position
        .center(0, turn2_z)
        .circle(tube_radius * 0.7)
        .extrude(-tube_radius * 4)
    )
    
    # Rundes Fenster hinten - Höhe der ersten Kurve (Turn 1)
    turn1_z = layer1_height + turn_radius
    turn1_y = outlet_length + layer1_len + turn_radius   # Hinter der Kurve

    window_back = (
        cq.Workplane("XZ")
        .workplane(offset=-turn1_y)
        .center(0, turn1_z)
        .circle(tube_radius * 0.7)
        .extrude(-tube_radius * 4)  # Nach hinten (+Y) extrudieren
    )
    
    return window_upper.union(window_lower).union(window_front).union(window_back)
    

# =============================================================================
# HOUSING
# =============================================================================

def make_storage(groove):
    """Create the housing box with the groove cut out."""
    
    bb = groove.val().BoundingBox()
    
    # Main box (upper part with open channel)
    box_length = bb.ymax - bb.ymin + 2 * wall_thickness - 2 * tube_radius
    box_width = bb.xmax - bb.xmin + 2 * wall_thickness + 0.2 * tube_radius
    box_height = bb.zmax - bb.zmin + wall_thickness - 1.7 * tube_radius
    
    box_center_x = (bb.xmax + bb.xmin) / 2
    box_center_y = (bb.ymax + bb.ymin + 2 * tube_radius) / 2
    box_center_z = (bb.zmax - 1.7 * tube_radius + bb.zmin) / 2
    
    box = (
        cq.Workplane("XY")
        .transformed(offset=(box_center_x, box_center_y, box_center_z))
        .box(box_width, box_length, box_height)
    )
    
    # Ground plate (lower part, fully enclosed tunnel)
    ground_length = bb.ymax - bb.ymin + 2 * wall_thickness
    ground_width = bb.xmax - bb.xmin + 2 * wall_thickness + 1 * tube_radius
    ground_height = 1.2 * tube_radius
    
    ground_center_x = (bb.xmax + bb.xmin) / 2
    ground_center_y = (bb.ymax + bb.ymin) / 2
    ground_center_z = -0.9 * tube_radius
    
    ground = (
        cq.Workplane("XY")
        .transformed(offset=(ground_center_x, ground_center_y, ground_center_z))
        .box(ground_width, ground_length, ground_height)
    )
    
    if enable_fillet:
        try:
            ground = ground.edges("|Z").fillet(fillet_radius)
        except:
            pass
        
        try:
            box = box.edges(">Z").fillet(fillet_radius)
        except:
            pass
        
        try:
            box = box.edges("|Z").fillet(fillet_radius)  # Vertikale Kanten
        except:
            pass
    
    result = box.union(ground).cut(groove)
    
    if enable_windows:
        windows = make_windows()
        if windows:
            result = result.cut(windows)
    
    return result

# =============================================================================
# BUILD
# =============================================================================

path = make_marble_path()
groove = make_groove_solid(path)
storage = make_storage(groove)
windows = make_windows()

# Export (uncomment to save)
# cq.exporters.export(storage, "kullerbue_storage.stl")