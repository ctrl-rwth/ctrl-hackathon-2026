# Construction Robotics Hackathon 2026

27–29 Nov 2026 · CTRL Lab Aachen

Code for the five challenges. One folder per challenge.

**Data, robot docs and simulation are on Hugging Face:** [ctrl-rwth/hackathon-2026](https://huggingface.co/datasets/ctrl-rwth/hackathon-2026) (gated, request access there).

```bash
pip install -U huggingface_hub
hf auth login
hf download ctrl-rwth/hackathon-2026 --repo-type dataset --local-dir hackathon-2026
```

| Folder | Challenge | Robot | Data |
|---|---|---|---|
| [eyes-in-the-sky](eyes-in-the-sky) | Eyes in the Sky | data only | [HF](https://huggingface.co/datasets/ctrl-rwth/hackathon-2026/tree/main/challenges/eyes-in-the-sky) |
| [weld-the-cage](weld-the-cage) | Weld the Cage | ABB GoFa + 3D camera | [HF](https://huggingface.co/datasets/ctrl-rwth/hackathon-2026/tree/main/challenges/weld-the-cage) |
| [site-safety-patrol](site-safety-patrol) | Site Safety Patrol | Unitree B2 | [HF](https://huggingface.co/datasets/ctrl-rwth/hackathon-2026/tree/main/challenges/site-safety-patrol) |
| [insulate-the-wall](insulate-the-wall) | Insulate the Wall | Unitree G1 | [HF](https://huggingface.co/datasets/ctrl-rwth/hackathon-2026/tree/main/challenges/insulate-the-wall) |
| [paving-the-way](paving-the-way) | Paving the Way | ABB GoFa on a Clearpath Husky | [HF](https://huggingface.co/datasets/ctrl-rwth/hackathon-2026/tree/main/challenges/paving-the-way) |

[ctrl-rwth.de](https://www.ctrl-rwth.de) · [Hugging Face](https://huggingface.co/ctrl-rwth)
