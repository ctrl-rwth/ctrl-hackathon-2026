# Inspire RH56DFQ hands

The Unitree G1 in the lab has **Inspire Robots RH56DFQ** dexterous hands, not the standard Unitree hands. The label on the left hand says **RH56DFQ-2L**.

Each hand has 6 motors (thumb yaw, thumb pitch, index, middle, ring, pinky) and 12 joints: the outer finger joints follow the motors.

## Files

| File | What |
|---|---|
| [g1_29dof_rev_1_0_with_inspire_hand_DFQ.urdf](g1_29dof_rev_1_0_with_inspire_hand_DFQ.urdf) | Whole G1 (29 DoF) with both hands |
| [DFQ_left_hand.urdf](DFQ_left_hand.urdf) | Left hand alone |
| [DFQ_right_hand.urdf](DFQ_right_hand.urdf) | Right hand alone |
| [config.yaml](config.yaml) | Links and joints that are removed from the G1 when these hands go on |
| [meshes](meshes) | STL meshes used by the URDFs |

Mesh paths in the URDFs are relative (`meshes/...`), so keep the folder together.

## Source

From Unitree's [unitree_ros](https://github.com/unitreerobotics/unitree_ros/tree/master/robots/g1_description), copied on 27 Nov 2026. BSD 3-Clause, see [LICENSE](LICENSE).
