# StrataCobot Workspace Functionality and Objectives

## 1. Workspace Overview

This repository is the e-Yantra Robotics Competition 2026-27 **StrataCobot (SC)** ROS 2 workspace.

The workspace targets:

- Ubuntu 24.04
- ROS 2 Jazzy
- Gazebo Harmonic / gz-sim 8
- A UR7e robotic arm with a mast-mounted RealSense camera
- An eBot mobile robot
- A simulated mining arena containing ores, rocks, a conveyor/table area, and an ore package

The repository supplies the simulation, robot descriptions, task launch files, RViz configurations, and starter algorithm files. It does **not** automatically run a completed solution node. The task solution must be written in the `algorithms` package.

## 2. Repository Components

### `algorithms/`

An `ament_python` ROS 2 package intended for student task nodes.

Package dependencies include:

- `rclpy`
- `geometry_msgs`
- `sensor_msgs`
- `std_msgs`
- `std_srvs`
- `control_msgs`
- `controller_manager_msgs`
- `tf2_ros`

The package contains three starter files:

- `boilerplate/task1a_boilerplate.py`: starter for camera-based ore perception
- `boilerplate/task1b_boilerplate.py`: starter for UR7e waypoint manipulation
- `boilerplate/task1c_boilerplate.py`: starter for eBot route navigation

The solution directories are:

- `scripts/task1a/`
- `scripts/task1b/`
- `scripts/task1c/`

At the time this document was created, these directories contain only `.gitkeep` files. No completed task executable is registered in `algorithms/setup.py`; its `SCRIPTS` list is empty.

A solution script must:

1. Be copied from the relevant boilerplate into the appropriate `scripts/task1x/` directory.
2. Start with `#!/usr/bin/env python3`.
3. Be executable with `chmod +x`.
4. Be added to the `SCRIPTS` list in `algorithms/setup.py`.
5. Be installed by rebuilding the workspace before it is run with `ros2 run`.

For example:

```bash
cd algorithms
cp boilerplate/task1a_boilerplate.py scripts/task1a/ore_detector.py
chmod +x scripts/task1a/ore_detector.py
```

Then register it in `setup.py`:

```python
SCRIPTS = [
    'scripts/task1a/ore_detector.py',
]
```

### `eyantra_kepler_colony/`

The main simulation package. It provides:

- Task-specific launch files
- The Gazebo world and arena configuration
- Ore, rock, robot, and package model resources
- RViz configurations
- Environment and resource path setup

Its launch files intentionally start the environment only. The student algorithm node is started separately.

### `ur_description/`

The modified UR robot description package. It provides the UR7e model, URDF/Xacro files, controllers, camera configuration, sensor bridges, robot-state publishing, and the launch file used to place the arm in Gazebo.

### `ebot_description/`

The eBot mobile-base description package. It provides the eBot model, sensors, robot-state publishing, Gazebo integration, and its spawn launch file.

### `build/`, `install/`, and `log/`

These are generated colcon workspace directories:

- `build/`: intermediate build products
- `install/`: installed packages and executable scripts used by ROS 2
- `log/`: colcon build logs and metadata

The copy executed by `ros2 run` comes from `install/`, not directly from the source file in `algorithms/`.

### `eyrc-sc-evaluator`

The supplied evaluator executable records and scores a task run. The evaluator must be run with the simulation and workspace sourced. It produces a signed `result.zip` that must remain unchanged when preparing a submission.

## 3. General Build and Environment Workflow

From the workspace parent or the location expected by the local setup, install dependencies and build:

```bash
./requirements.sh
colcon build
source install/setup.bash
```

Every terminal used for ROS 2 commands must source the workspace. After changing a solution script, rebuild and source again:

```bash
colcon build --packages-select algorithms
source install/setup.bash
ros2 pkg executables algorithms
```

`ros2 pkg executables algorithms` is the direct check that a script has been installed. The executable name is the file name, including `.py`.

The standard simulation launch commands are:

```bash
ros2 launch eyantra_kepler_colony task0.launch.py
ros2 launch eyantra_kepler_colony task1a.launch.py
ros2 launch eyantra_kepler_colony task1b.launch.py
ros2 launch eyantra_kepler_colony task1c.launch.py
```

Use `rviz:=false` to suppress RViz. Use `gui:=false` for a headless Gazebo server where supported.

## 4. Task 0 Objective and Functionality

Task 0 is the base simulation setup and must be complete before Task 1 work begins.

Its purpose is to bring up the complete arena, including:

- The Gazebo Harmonic world
- The UR7e arm when enabled
- The eBot when enabled
- Ore samples, rocks, and the ore package when enabled
- The `/clock` bridge for simulation time
- Required Gazebo resource paths

The general Task 0 launch file supports options to enable or disable the arm, eBot, and objects. It starts the world first and uses delayed actions to spawn the robots and objects.

Task 0 is infrastructure rather than a solution algorithm. No student node is launched automatically.

## 5. Task 1A Objective: Ore Perception

### Objective

Task 1A is an image-processing and 3D localisation task. The solution must read the camera streams, detect all six ores, calculate their positions relative to `base_link`, and continuously publish one TF transform per ore.

For every ore, the node must:

1. Identify its type from the coloured top face.
2. Estimate the three-dimensional position of the top-face centre.
3. Transform that position into the `base_link` frame.
4. Publish a legal `tf2` transform continuously while the run is active.
5. Display the detections with boundaries and exact transform names in an OpenCV window.

There are six ores: two of each type.

| Ore colour | Ore type | Required transform names |
|---|---|---|
| Blue | Azurite | `azurite_ore_1`, `azurite_ore_2` |
| Green | Malachite | `malachite_ore_1`, `malachite_ore_2` |
| Orange | Vanadinite | `vanadinite_ore_1`, `vanadinite_ore_2` |

The IDs may be assigned in any consistent way, but the two ores of the same type must receive different IDs and retain those IDs during the run.

### Supplied camera interfaces

The UR7e camera bridge provides 640 x 480 streams:

| Topic | Message | Purpose |
|---|---|---|
| `/camera/camera/color/image_raw` | `sensor_msgs/msg/Image` | BGR colour image used for segmentation |
| `/camera/camera/aligned_depth_to_color/image_raw` | `sensor_msgs/msg/Image` | Depth aligned to colour pixels |
| `/camera/camera/color/camera_info` | `sensor_msgs/msg/CameraInfo` | Camera intrinsics |
| `/camera/camera/depth/color/points` | Point cloud | Optional bridged/developed point cloud support |
| `/tf` | TF stream | Camera-to-robot and solution transforms |

The colour, aligned depth, and camera-info messages are stamped in `camera_color_optical_frame`.

The optical-frame axes are:

- +X: right in the image
- +Y: down in the image
- +Z: forward along the camera view direction

### Expected processing pipeline

A complete Task 1A node should implement the following pipeline:

1. Convert the ROS colour image to an OpenCV BGR image through `cv_bridge`.
2. Convert BGR to HSV or another suitable colour space.
3. Threshold blue, green, and orange regions.
4. Clean masks with morphology and reject small contours.
5. Compute one centre pixel per ore.
6. Read a small depth window around each centre and use a robust statistic such as the median.
7. Convert depth to metres. `32FC1` depth is already in metres; `16UC1` depth is in millimetres and must be divided by 1000.
8. Read `fx`, `fy`, `cx`, and `cy` from `CameraInfo` rather than hardcoding them.
9. Deproject pixel `(u, v)` and depth `z` into the optical frame:

   ```text
   x = (u - cx) * z / fx
   y = (v - cy) * z / fy
   z = z
   ```

10. Transform the point from the camera optical frame into `base_link` using the TF buffer.
11. Correct the measured top-face point to the required ore centre where appropriate. The scoring target is based on the ore's physical centre, while the coloured face is the visible top face.
12. Match detections consistently to IDs across frames.
13. Publish every transform on every processing cycle, not only once.
14. Draw each boundary and exact transform name, then show the annotated frame with OpenCV.

Every published `TransformStamped` must have:

- `header.frame_id = 'base_link'`
- An exact required `child_frame_id`
- Translation values in metres
- A valid rotation, for example `rotation.w = 1.0` and `x = y = z = 0.0`
- A current timestamp

### Task 1A scoring requirements

The evaluator scores the transforms published while the node runs:

- Each correctly named ore within 0.05 m of the target earns 3 marks.
- Six correct ores provide 18 marks.
- If all six are within 0.03 m, a 2-mark all-or-nothing bonus is awarded.
- A transform with an incorrect child-frame name does not count.
- Publishing once or publishing only briefly is insufficient; estimates must be published continuously.

The task submission also requires an OpenCV detection-window snapshot showing all detected ores, each with a boundary and transform name.

### Task 1A launch behavior

`task1a.launch.py`:

- Starts Gazebo with the arena world.
- Starts the simulation clock bridge.
- Spawns the UR7e after a delay.
- Starts the camera colour and depth bridges through the UR description launch.
- Starts camera point-cloud support.
- Publishes the `map` to `world` static transform.
- Opens the Task 1A RViz configuration after a delay.
- Does not start an ore detector.

The node must be started separately after the simulation is running:

```bash
ros2 run algorithms <your_node>.py
```

The provided Task 1A boilerplate currently defines the subscriptions, TF buffer/listener, TF broadcaster, timer, and function structure, but leaves detection, callbacks, deprojection, transform publication, ID tracking, and display logic for implementation.

## 6. Task 1B Objective: UR7e Waypoint Manipulation

### Objective

Task 1B requires the solution to drive the UR7e tool through five Cartesian waypoints in order and hold at each waypoint for at least two seconds.

The starter waypoint list in the boilerplate is:

```text
(-0.4085, -0.5379, 0.1967)
(-0.8000, -0.0005, 0.3967)
(-0.7430,  0.5280, 0.1967)
(-0.4097,  0.5280, 0.1967)
(-0.0763,  0.5280, 0.1967)
```

Coordinates are in metres in `base_link`.

### Supplied interfaces

The arm task provides:

- `/tcp_pose_raw`: current tool-tip pose
- `/ur7e/end_effector/force_magnitude`: filtered tool force
- `/arm_status`: servo state
- `/magnet_status`: magnet holding state
- `/magnet`: `std_srvs/SetBool` service for grip/release
- TF from `base_link` to the tool frame

The Cartesian servo is already running. A solution should command the servo rather than directly taking over the underlying controller.

The boilerplate identifies two command interfaces:

- `/ur_arm_controller/delta_twist_controller`
- `/ur_arm_controller/delta_joint_controller`

Only one command interface is active at a time. Command limits in the starter are 0.15 m/s linear, 0.35 rad/s angular, and 0.35 rad/s per joint. The servo has a dead-man timeout of 0.15 seconds, so commands must be sent continuously while moving.

### Task 1B launch behavior

`task1b.launch.py` starts the arena and UR7e on a clear table, disables the arena plugin, does not spawn ores or the eBot, and opens the Task 1B RViz configuration. It does not run a manipulation node.

The Task 1B boilerplate contains the waypoint constants and ROS interface setup, but the control logic, waypoint progression, holding behavior, safety limits, and completion handling are not implemented.

## 7. Task 1C Objective: eBot Navigation

### Objective

Task 1C requires the eBot to follow the route published by the arena, in waypoint order, while navigating around obstacles and stopping after the route is complete.

The solution must:

1. Receive the route.
2. Track current position and heading from odometry.
3. Use lidar data to detect nearby obstacles.
4. Choose safe steering behavior around obstacles.
5. Publish bounded velocity commands.
6. Verify progress using odometry rather than assuming commands equal motion.
7. Stop the base after the final waypoint.
8. Keep the node alive and avoid uncaught exceptions that could leave the base moving.

### Supplied interfaces

| Topic/service | Type | Purpose |
|---|---|---|
| `/ebot_path` | `nav_msgs/msg/Path` | Latched route and ordered waypoints |
| `/map` | `nav_msgs/msg/OccupancyGrid` | Arena ground-truth map |
| `/scan` | `sensor_msgs/msg/LaserScan` | 360-sample 2D lidar scan over approximately +/- 1.57 rad |
| `/odom` | `nav_msgs/msg/Odometry` | Wheel odometry and current pose |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | Linear and angular base command |

The route is published once before a late-starting node may exist, so the path subscription must use compatible transient-local QoS. The starter command limits are 0.5 m/s linear and 1.0 rad/s angular.

### Task 1C launch behavior

`task1c.launch.py`:

- Starts the arena world.
- Enables the random rock map.
- Enables route publication on `/ebot_path`.
- Spawns the eBot after a delay.
- Publishes `map` to `world`.
- Opens the Task 1C RViz configuration.
- Does not start a path follower.

The Task 1C boilerplate provides subscriptions, a command publisher, a timer, and navigation constants, but leaves QoS correction, route storage, odometry parsing, lidar processing, obstacle avoidance, waypoint control, and stopping behavior to be implemented.

## 8. Simulation Models and Spawned Objects

The arena resource package contains models for:

- `azurite_ore`
- `malachite_ore`
- `vanadinite_ore`
- `ore_package`
- `rocks`
- `arm_base`
- `kepler_world`

The ore SDF files define each ore as a movable model with a collision box of:

- Width: 0.1016 m
- Length: 0.1016 m
- Height: 0.0762 m
- Mass: 0.15 kg

The object-spawn launch file creates two instances of each ore type, along with an ore package and seven rocks. In the checked-in launch configuration, the ore positions are declared in the spawn list, but the Task 1A instructions require a detector to use the camera rather than hardcode positions because evaluator/session placement can be randomised.

## 9. RViz and Observation Tools

The simulation package supplies separate RViz configurations:

- `rviz/task1a.rviz`: Task 1A camera/TF inspection
- `rviz/task1b.rviz`: Task 1B arm/waypoint inspection
- `rviz/task1c.rviz`: Task 1C navigation inspection

Useful runtime checks include:

```bash
ros2 node list
ros2 topic list
ros2 topic echo /camera/camera/color/camera_info
ros2 topic info /ebot_path -v
ros2 run tf2_ros tf2_echo base_link azurite_ore_1
```

For Task 1A, `tf2_echo` should show one transform for each exact ore child-frame name, with `base_link` as the parent.

## 10. Evaluator and Submission Objective

The evaluator is intended to run after the relevant simulation and solution node are ready. For Task 1B, the root README documents the general form:

```bash
./eyrc-sc-evaluator --task 1B --team-id 1455
```

The task and team arguments may be supplied interactively when omitted. The evaluator reports readiness, records the run, and writes a signed `result.zip` into a team/task directory. The result archive must not be unpacked, rebuilt, edited, or renamed internally.

The final submission archive and node filename depend on the task page. The archive should contain the evaluator result and the task solution file using exactly the names and structure specified for that task.

## 11. Current Implementation Status

| Area | Status |
|---|---|
| ROS 2 package structure | Present |
| Gazebo world and resource paths | Present |
| UR7e description and camera bridge | Present |
| eBot description and launch support | Present |
| Task 0 simulation launch | Present |
| Task 1A launch and RViz setup | Present |
| Task 1B launch and RViz setup | Present |
| Task 1C launch and RViz setup | Present |
| Task 1A completed solution node | Not present |
| Task 1B completed solution node | Not present |
| Task 1C completed solution node | Not present |
| Algorithm executables registered in `setup.py` | None |
| End-to-end task scoring | Not yet available until a solution is implemented and registered |

The repository is therefore a simulation and starter-code workspace. Its primary remaining objective is to implement, register, build, and validate the three task solution nodes against the supplied launch environments and evaluator.

## 12. Main Objectives Summary

1. Maintain a buildable ROS 2 Jazzy/Gazebo Harmonic workspace.
2. Bring up the correct simulation for each task.
3. Implement Task 1A ore classification, 3D localisation, and continuous TF publication.
4. Implement Task 1B UR7e waypoint control with safe, bounded commands and required holds.
5. Implement Task 1C eBot route following with lidar-based obstacle avoidance and reliable stopping.
6. Rebuild and source the installed workspace after every algorithm change.
7. Verify topics, frames, executable registration, and runtime behavior before evaluation.
8. Produce the exact task-specific submission archive without modifying evaluator output.
