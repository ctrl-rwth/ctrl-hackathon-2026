# Writes wall.xml: assembly table, timber-frame wall mock-up lying flat (open bays facing up) and one soft
# insulation batt above the first bay. scene_wall.xml loads it together with the G1.
# Change the numbers below to match the real mock-up, then run:  python make_wall.py
#
# The real mock-up size was not known when this was made. Defaults are a typical German timber-frame wall:
# studs 60 x 160 mm on a 625 mm grid, so each bay is 565 mm wide and 160 mm deep.

# --- mock-up (metres) ---
TABLE_TOP = 0.40      # height of the assembly table top (built low for the 1.3 m tall G1)
WALL_NEAR = 0.25      # distance from the robot (pelvis) to the near edge of the wall
N_BAYS = 2            # bays side by side; bay 1 is straight in front of the robot
GRID = 0.625          # stud spacing, centre to centre
STUD_W = 0.06         # stud width
STUD_D = 0.16         # stud depth = insulation thickness
BAY_LEN = 0.60        # clear length of a bay, between the two plates
BOARD = 0.015         # sheathing board under the frame (closes the bays at the bottom)

# --- insulation batt ---
BATT_OVERSIZE = 0.01  # batts are cut about 1 cm wider than the bay so they clamp
BATT_MASS = 2.0       # kg (mineral wool ~35 kg/m3; wood fibre is ~50 kg/m3, heavier and stiffer)
BATT_YOUNG = 1e4      # Pa, stiffness: with 1 cm oversize the batt sticks halfway, ~80 N presses it in
BATT_POISSON = 0.1
BATT_DAMPING = 0.002
BATT_COUNT = (7, 7, 3)  # points along length, width, thickness (more = softer look, slower sim)
BATT_RADIUS = 0.006   # contact radius of each point; the outer size of the batt includes it

import os

HERE = os.path.dirname(os.path.abspath(__file__))


def box(name, center, half, material):
    c = " ".join(f"{v:.4f}" for v in center)
    h = " ".join(f"{v:.4f}" for v in half)
    return f'      <geom name="{name}" type="box" pos="{c}" size="{h}" material="{material}"/>'


def main():
    bay_x0 = WALL_NEAR + STUD_W              # bays start after the near plate
    bay_x1 = bay_x0 + BAY_LEN
    wall_x1 = bay_x1 + STUD_W
    studs_y = [GRID / 2 - k * GRID for k in range(N_BAYS + 1)]  # bay 1 is centred on y = 0
    y_min, y_max = min(studs_y) - STUD_W / 2, max(studs_y) + STUD_W / 2
    z_board = TABLE_TOP + BOARD
    z_mid = z_board + STUD_D / 2
    table_half = ((wall_x1 - WALL_NEAR) / 2 + 0.1, (y_max - y_min) / 2 + 0.1)
    table_c = ((WALL_NEAR + wall_x1) / 2, (y_min + y_max) / 2)

    g = []
    g.append(box("table_top", (*table_c, TABLE_TOP - 0.02), (*table_half, 0.02), "steel"))
    for i, (sx, sy) in enumerate([(1, 1), (1, -1), (-1, 1), (-1, -1)]):
        lx = table_c[0] + sx * (table_half[0] - 0.04)
        ly = table_c[1] + sy * (table_half[1] - 0.04)
        g.append(box(f"table_leg{i}", (lx, ly, (TABLE_TOP - 0.04) / 2), (0.03, 0.03, (TABLE_TOP - 0.04) / 2), "steel"))
    g.append(box("board", ((WALL_NEAR + wall_x1) / 2, (y_min + y_max) / 2, TABLE_TOP + BOARD / 2),
                 ((wall_x1 - WALL_NEAR) / 2, (y_max - y_min) / 2, BOARD / 2), "board"))
    for i, y in enumerate(studs_y):
        g.append(box(f"stud{i}", ((bay_x0 + bay_x1) / 2, y, z_mid), (BAY_LEN / 2, STUD_W / 2, STUD_D / 2), "timber"))
    for name, x in (("plate_near", WALL_NEAR + STUD_W / 2), ("plate_far", bay_x1 + STUD_W / 2)):
        g.append(box(name, (x, (y_min + y_max) / 2, z_mid), (STUD_W / 2, (y_max - y_min) / 2, STUD_D / 2), "timber"))

    # One invisible box site per bay: the space the insulation has to fill (used to measure fill quality).
    sites = []
    for b in range(N_BAYS):
        yc = (studs_y[b] + studs_y[b + 1]) / 2
        sites.append(f'      <site name="bay{b + 1}" type="box" pos="{(bay_x0 + bay_x1) / 2:.4f} {yc:.4f} {z_mid:.4f}" '
                     f'size="{BAY_LEN / 2:.4f} {(GRID - STUD_W) / 2:.4f} {STUD_D / 2:.4f}" rgba="0 0 0 0" group="5"/>')

    nx, ny, nz = BATT_COUNT
    r = BATT_RADIUS
    # Outer size (with the contact radius): as long as the bay, BATT_OVERSIZE wider, as thick as the studs.
    blen, bwid, bthk = BAY_LEN - 2 * r - 0.004, GRID - STUD_W + BATT_OVERSIZE - 2 * r, STUD_D - 2 * r
    spacing = (blen / (nx - 1), bwid / (ny - 1), bthk / (nz - 1))
    batt_z = z_board + STUD_D + STUD_D / 2 + 0.01  # lying on top of bay 1, 1 cm above the studs
    batt = f'''    <flexcomp name="batt" type="grid" dim="3" count="{nx} {ny} {nz}"
              spacing="{spacing[0]:.4f} {spacing[1]:.4f} {spacing[2]:.4f}"
              pos="{(bay_x0 + bay_x1) / 2:.4f} 0 {batt_z:.4f}" radius="{r}" mass="{BATT_MASS}" rgba="0.95 0.78 0.3 1">
      <contact condim="3" selfcollide="none" solref="0.01 1"/>
      <elasticity young="{BATT_YOUNG:g}" poisson="{BATT_POISSON}" damping="{BATT_DAMPING}"/>
    </flexcomp>'''

    xml = f'''<!-- Made by make_wall.py: change the numbers there and run it again. -->
<mujoco model="insulate_the_wall_mockup">
  <asset>
    <material name="steel" rgba="0.55 0.57 0.6 1" specular="0.3"/>
    <material name="board" rgba="0.82 0.74 0.58 1"/>
    <material name="timber" rgba="0.78 0.6 0.38 1"/>
  </asset>
  <worldbody>
    <body name="mockup">
{chr(10).join(g)}
{chr(10).join(sites)}
    </body>
{batt}
  </worldbody>
</mujoco>
'''
    with open(os.path.join(HERE, "wall.xml"), "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"wrote wall.xml: {N_BAYS} bays of {GRID - STUD_W:.3f} x {BAY_LEN:.2f} x {STUD_D:.2f} m, "
          f"table top {TABLE_TOP:.2f} m, stud tops at {z_board + STUD_D:.3f} m")


if __name__ == "__main__":
    main()
