
# An Integrated Task and Motion Planning Framework for Dynamic Locomotion

This repository contains code to generate an integrated task and motion planners for dynamic bipedal locomotion in partially observable environments with multi-level safety guarantees. This layered planning framework is composed of a high-level symbolic task planner and a low-level phase-space motion planner. The symbolic task planner is further divided into a navigation planner and an action planner. The synthesized navigation planner plays a two player navigation and collision avoidance game against a possibly adversarial environment. The action planner guarantees safe actions, resulting in the desired transition in the navigation game, are generated at each walking step. The low-level phase-space planner uses a reduced-order prismatic inverted pendulum locomotion model to generate non-periodic trajectories meeting balancing safety criteria for straight and steering walking. These criteria are characterized by constraints on locomotion keyframe states, and are used to define keyframe transition policies via viability kernels. 


# Task Planner

The task_planner directory contains the code necessary to synthesize navigation and action planners for bipedal locomotion in a partially observable environment. The planners can be simulated in a discrete 2D game against a user controlled dynamic obstacle. The discrete obstacle trajectory and action sets at each robot keyframe are stored in an output file that are used by the motion planner to plan robot trajectories and simulate the resulting locomotion behavior in drake.

## Synthesis

We have included the [slugs](http://motesy.cs.uni-bremen.de/pdfs/cav2016.pdf) reactive synthesis tool developed by Rüdiger Ehlers and Vasumathi Raman, which needs to be installed for navigation and action planning synthesis. Documentation can be found [here](https://github.com/VerifiableRobotics/slugs). If you already have slugs installed, then you must simply change the path in [Run_File_coarse_abstraction_CDC.py](task_planner/Bipedal_Locomotion_Task_Planner/safe-nav-loco/Run_File_coarse_abstraction_CDC.py) and [Run_File_fine_abstraction.py](task_planner/Bipedal_Locomotion_Task_Planner/safe-nav-loco/Run_File_fine_abstraction.py).

## Running the code

Synthesis and 2D simulation code requires python 2.7

### Environment input file

The code requires an image of the environment as an input. White areas in the image are interpreted as obstacle free, while black areas are interpreted as static obstacles. If the discrete representation of the environment is already known, an image can be generated pixel by pixel using [PNG_Gen.py](/task_planner/PNG_Gen/PNG_Gen.py).

### Synthesis

Synthesis of the navigation planner is executed by running [Run_File_coarse_abstraction_CDC.py](task_planner/Bipedal_Locomotion_Task_Planner/safe-nav-loco/Run_File_coarse_abstraction_CDC.py) (the desired discrete abstraction, belief partition, and initial robot and obstacle locations can also be edited in this file).

`cd task_planner/Bipedal_Locomotion_Task_Planner/safe-nav-loco/; python Run_File_coarse_abstraction_CDC.py`

Synthesis of the action planner is executed by running [Run_File_fine_abstraction.py](task_planner/Bipedal_Locomotion_Task_Planner/safe-nav-loco/Run_File_fine_abstraction.py).

`python Run_File_fine_abstraction.py`


### 2D simulation

After synthesis is complete both planners can be simulated in a 2D collision avoidance game against a user controlled dynamic obstacle. Run [Sim_2LA.py](task_planner/Bipedal_Locomotion_Task_Planner/safe-nav-loco/Sim_2LA.py) to initiate the simulation. 

`python Sim_2LA.py`

The user can control the dynamic obstacle on the coarse grid using the arrow keys. Between coarse game states the code visualizes the robot progressing through the environment on a fine discretization within one discrete coarse cell. Actions at each keyframe as well as the dynamic obstacle pass are saved into an output file in the [integration](task_planner/Bipedal_Locomotion_Task_Planner/safe-nav-loco/Examples/Integration) directory. 

<img src="/task_planner/Bipedal_Locomotion_Task_Planner/safe-nav-loco/Examples/figs/oPcD42B.gif" />



## Acknowledgment

We would like to acknowledge Suda Bharadwaj and Ufuk Topcu for their discussions on belief space planning [implementation](https://github.com/u-t-autonomous/Surveillance-Synthesis) which this code builds upon.

# Motion Planner

The motion_planner directory contains the code necessary to generate the center of mass, foot trajectories as well as foot placement location using phase-space planning. It also contains a Drake visualization code of the Cassie bipedal robot following the generated trajectories in the proposed environment.

## Drake Phase-Space Planning and Visualization 

The code is based on Drake (Please see the [Drake Documentation](https://drake.mit.edu) for more
information). Here we include the source code of Drake and our own addition for phase-space planning in the [safe-nav-loco](motion_planner/drake/safe-nav-loco/) folder.

The code is run on Ubuntu 16.04.

## Initializing 

In a terminal go to the directory where you want to clone safe-nav-locomotion repo.
run 
`git clone https://github.com/GTLIDAR/safe-nav-locomotion.git`

### Building Drake
Make sure you have the required dependencies for Drake. 
Drake installation steps can be found [here](https://drake.mit.edu/installation.html).

### Local adjustments 

in [motion_planner/drake/safe-nav-loco/src/simulate_psp.cc](motion_planner/drake/safe-nav-loco/src/simulate_psp.cc) and [motion_planner/drake/safe-nav-loco/src/run_cassie_follow.cc](motion_planner/drake/safe-nav-loco/src/run_cassie_follow.cc) adjust the path in `file_name = "path/drake/safe-nav-loco/vis/..."` to match the path to the drake directory on your local machine. 

## Running the code
### Setting up action.json file from task_planner
* Once an action.json file is generated from task_planner, copy and paste the file into [motion_planner/drake/safe-nav-loco/vis/](motion_planner/drake/safe-nav-loco/vis/).
Note:[actions_CDC_Subs.json](motion_planner/drake/safe-nav-loco/vis/actions_CDC_Sub.json) is the action file used in our publication

* In [motion_planner/drake/safe-nav-loco/src/simulate_psp.cc](motion_planner/drake/safe-nav-loco/src/simulate_psp.cc) adjust the path in 
`BeliefIOParser parser("path/drake/safe-nav-loco/vis/actions_CDC_Sub.json");` and choose the desired action file.

### Phase-Space Planning and trajectory generation 
* Open terminal and go to the drake folder `cd path/drake/`

* run `CC=clang-6.0 CXX=clang++-6.0 bazel run safe-nav-loco:simulate_psp`
This will generate the trajectory .txt files.

### Drake Visualization 
<img src="https://i.imgur.com/taoI3AF.gif" />

Make sure that the trajectories are generated beforehand as shown in the previous section.

* Open terminal and run the command to open Drake visualizer
```
cd path/drake/
bazel-bin/tools/drake_visualizer
```
In case the Drake visualizer is not built already run the following command
```
bazel build //tools:drake_visualizer
```
* Open another terminal and run the command to open the drake-lcm-spy
```
cd path/drake/
bazel-bin/lcmtypes/drake-lcm-spy
```
In case the drake-lcm-spy is not built already run the following command
```
bazel build //lcmtypes:drake-lcm-spy
```
* Open a third terminal and run the command to simulate the Cassie robot in drake visualizer within the environment
```
cd path/drake/
CC=clang-6.0 CXX=clang++-6.0 bazel run safe-nav-loco:run_cassie_follow
```

### Py.plot Visualization 
<img src="https://i.imgur.com/jJ5KXOj.png" />

* Open terminal and run the command to visualize the center of mass and foot trajectories as well as high-level waypoints, and foot stance locations.

```
cd path/drake/safe-nav-loco/vis/
python vis_psp.py 
```


# Project and Related Publications 

This work is a part of our ongoing work on robust and reactive decision-making and AI planning of collaborative and agile robots in complex environments. More information and related publications can be found [here](http://lab-idar.gatech.edu/robust-and-reactive-decision-making-and-ai-planning-of-collaborative-and-agile-robots-in-complex-environments/)


This repo contains the code used for implementation in our [published work](https://arxiv.org/abs/2009.05168):-
```
@article{warnketowards,
  title={Towards Safe Locomotion Navigation in 
  Partially Observable Environments with Uneven Terrain},
  author={Warnke, Jonas and Shamsah, Abdulaziz 
  and Li, Yingke and Zhao, Ye}
  journal   = {IEEE Conference on Decision and Control},
  year      = {2020},
}
```

### Reference Citation

[Jonas Warnke*, Abdulaziz Shamsah*, Yingke Li*, and Ye Zhao. Towards Safe Locomotion Navigation in Partially Observable Environments with Uneven Terrain, (*equally contributed), IEEE Conference on Decision and Control, 2020.](https://arxiv.org/abs/2009.05168)


# About
