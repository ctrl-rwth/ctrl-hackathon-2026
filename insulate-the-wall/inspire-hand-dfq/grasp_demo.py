# Opens the G1 with Inspire RH56DFQ hands in the MuJoCo viewer and slowly closes and opens both hands.
#   pip install mujoco
#   python grasp_demo.py          (on macOS: mjpython grasp_demo.py)
import math
import os
import time

import mujoco
import mujoco.viewer

HERE = os.path.dirname(os.path.abspath(__file__))
model = mujoco.MjModel.from_xml_path(os.path.join(HERE, "scene.xml"))
data = mujoco.MjData(model)

FINGER = ("thumb", "index", "middle", "ring", "pinky")
fingers = [i for i in range(model.nu) if any(k in model.actuator(i).name for k in FINGER)]

with mujoco.viewer.launch_passive(model, data) as viewer:
    start = time.time()
    while viewer.is_running():
        t = time.time() - start
        close = 0.5 - 0.5 * math.cos(t * 1.5)  # 0 = open, 1 = closed
        for i in fingers:
            low, high = model.actuator_ctrlrange[i]
            data.ctrl[i] = low + close * (high - low)
        mujoco.mj_step(model, data)
        viewer.sync()
        time.sleep(model.opt.timestep)
