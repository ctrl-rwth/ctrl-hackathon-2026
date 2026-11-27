# Builds g1_inspire_dfq.xml (MuJoCo) from Unitree's URDF of the G1 with Inspire RH56DFQ hands.
# You only need this if you change the URDF; g1_inspire_dfq.xml is already in the folder.
#   pip install mujoco
#   python build_mjcf.py
import os
import xml.etree.ElementTree as ET

import mujoco

HERE = os.path.dirname(os.path.abspath(__file__))
URDF = os.path.join(HERE, "g1_29dof_rev_1_0_with_inspire_hand_DFQ.urdf")
OUT = os.path.join(HERE, "g1_inspire_dfq.xml")
PELVIS_HEIGHT = 0.793  # standing height of the pelvis, same as Unitree's own G1 MuJoCo model
FINGER = ("thumb", "index", "middle", "ring", "pinky")


def gains(joint):
    """(kp, damping, armature) per joint group. Fingers get armature so the tiny finger links stay stable."""
    n = joint.lower()
    if any(k in n for k in FINGER):
        return 2.0, 0.1, 0.005
    if "wrist" in n:
        return 20.0, 1.0, 0.01
    if "shoulder" in n or "elbow" in n:
        return 80.0, 3.0, 0.02
    return 150.0, 5.0, 0.02  # legs and waist


def main():
    urdf = ET.parse(URDF).getroot()
    mimic = {}  # follower joint -> (leader joint, multiplier, offset)
    for j in urdf.findall("joint"):
        m = j.find("mimic")
        if m is not None:
            mimic[j.get("name")] = (m.get("joint"), float(m.get("multiplier", 1)), float(m.get("offset", 0)))

    # Let MuJoCo's own URDF importer do the conversion.
    for old in urdf.findall("mujoco"):
        urdf.remove(old)
    ext = ET.SubElement(urdf, "mujoco")
    ET.SubElement(ext, "compiler", meshdir=".", balanceinertia="true", discardvisual="false", fusestatic="false")
    tmp = os.path.join(HERE, "_tmp_import.urdf")
    ET.ElementTree(urdf).write(tmp)
    try:
        model = mujoco.MjModel.from_xml_path(tmp)
        mujoco.mj_saveLastXML(OUT, model)
    finally:
        os.remove(tmp)

    mj = ET.parse(OUT).getroot()
    mj.set("model", "g1_inspire_dfq")
    for mesh in mj.iter("mesh"):
        mesh.attrib.pop("content_type", None)  # older MuJoCo versions do not know it; the .STL ending is enough
    for old in mj.findall("option"):
        mj.remove(old)
    mj.insert(1, ET.Element("option", timestep="0.002", integrator="implicitfast"))

    # Hang the robot at standing height with a fixed pelvis: no balance controller needed for arm and hand work.
    world = mj.find("worldbody")
    pelvis = world.find("body[@name='pelvis']")
    if pelvis is None:
        pelvis = ET.Element("body", name="pelvis", pos="0 0 0")
        for child in list(world):
            world.remove(child)
            pelvis.append(child)
        world.append(pelvis)
    pelvis.set("pos", f"0 0 {PELVIS_HEIGHT}")

    joints = [j for j in world.iter("joint") if j.get("type", "hinge") == "hinge"]
    for old in mj.findall("actuator"):
        mj.remove(old)
    actuators = ET.SubElement(mj, "actuator")
    for j in joints:
        name = j.get("name")
        kp, damping, armature = gains(name)
        j.set("damping", str(damping))
        j.set("armature", str(armature))
        if name in mimic:
            continue  # moved by an equality constraint, not by a motor
        a = ET.SubElement(actuators, "position", name=name.replace("_joint", ""), joint=name, kp=str(kp))
        if j.get("range"):
            a.set("ctrlrange", j.get("range"))
            a.set("ctrllimited", "true")

    # URDF <mimic> becomes a joint equality: follower = offset + multiplier * leader.
    # Newer MuJoCo versions already do this in the importer; add only the ones that are missing.
    eq = mj.find("equality")
    if eq is None:
        eq = ET.SubElement(mj, "equality")
    have = {e.get("joint1") for e in eq.findall("joint")}
    for follower, (leader, mult, off) in mimic.items():
        if follower not in have:
            ET.SubElement(eq, "joint", joint1=follower, joint2=leader, polycoef=f"{off} {mult} 0 0 0")
    if not len(eq):
        mj.remove(eq)

    ET.indent(mj)
    ET.ElementTree(mj).write(OUT, encoding="unicode")
    check = mujoco.MjModel.from_xml_path(OUT)
    print(f"wrote {os.path.basename(OUT)}: {check.nbody} bodies, {check.njnt} joints, {check.nu} motors, {check.neq} mimic constraints")


if __name__ == "__main__":
    main()
