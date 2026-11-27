# Wall mock-up demo: the insulation batt (1 cm wider than the bay) drops onto bay 1 and gets stuck halfway,
# then a push from above (an outside force, not the robot) presses it in. The fill is printed every second.
#   pip install mujoco
#   python insulation_demo.py          (on macOS: mjpython insulation_demo.py)
# Use fill_report() in your own code to measure how well your robot fills the bay.
import os
import time

import mujoco
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def batt_points(model, data, name="batt"):
    """Positions of the batt's points (N x 3) and the body id of each point."""
    f = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_FLEX, name)
    a, n = model.flex_vertadr[f], model.flex_vertnum[f]
    return data.flexvert_xpos[a:a + n].copy(), model.flex_vertbodyid[a:a + n]


def fill_report(model, data, bay="bay1", batt="batt"):
    """How well the batt fills a bay.
    inside:     share of batt points inside the bay (1.0 = all of it is in)
    sticking:   share of points still above the stud tops
    bottom_gap: mean gap (mm) between the lowest layer of the batt and the board under the bay (0 = touching)
    """
    s = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, bay)
    c, h = data.site_xpos[s], model.site_size[s]
    p, _ = batt_points(model, data, batt)
    radius = model.flex_radius[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_FLEX, batt)]
    tol = 0.01
    top, bottom = c[2] + h[2], c[2] - h[2]
    inside = np.all(np.abs(p[:, :2] - c[:2]) <= h[:2] + tol, axis=1) & (p[:, 2] <= top) & (p[:, 2] >= bottom - tol)
    z = np.sort(p[:, 2])
    lowest = z[: max(1, len(z) // 3)]  # bottom layer of the batt
    return {
        "inside": float(inside.mean()),
        "sticking": float((p[:, 2] > top + tol).mean()),
        "bottom_gap_mm": float(max(0.0, lowest.mean() - radius - bottom) * 1000),
    }


def main():
    import mujoco.viewer

    model = mujoco.MjModel.from_xml_path(os.path.join(HERE, "scene_wall.xml"))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    p, bodies = batt_points(model, data)
    top_layer = bodies[p[:, 2] > p[:, 2].max() - 1e-4]
    press = 80.0  # N, spread over the top layer

    with mujoco.viewer.launch_passive(model, data) as viewer:
        last = 0.0
        while viewer.is_running():
            t = data.time % 8.0  # every 8 s: rest 2 s, press 3 s, rest 3 s
            data.xfrc_applied[top_layer, 2] = -press / len(top_layer) if 2.0 <= t < 5.0 else 0.0
            step_start = time.time()
            mujoco.mj_step(model, data)
            viewer.sync()
            if data.time - last >= 1.0:
                last = data.time
                r = fill_report(model, data)
                print(f"t={data.time:5.1f}s  inside {r['inside']:.0%}  sticking out {r['sticking']:.0%}  bottom gap {r['bottom_gap_mm']:.0f} mm")
            time.sleep(max(0.0, model.opt.timestep - (time.time() - step_start)))


if __name__ == "__main__":
    main()
