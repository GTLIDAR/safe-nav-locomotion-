# Motion Planner
## Drake Phase-Space Planning and Visualization 

The code is based on Drake (Please see the [Drake Documentation](https://drake.mit.edu) for more
information). Here we include the source code of Drake and our own addition for phase-space planning in the CDC folder.

The code is run on Ubuntu 16.04.

## Initialzing 

### Building Drake
Setup Drake following the step by step tutorial [here](https://drake.mit.edu/installation.html).

### Local adjustments 

in [Motion_Planner/drake/CDC/src/simulate_psp.cc](Motion_Planner/drake/CDC/src/simulate_psp.cc) and [Motion_Planner/drake/CDC/src/run_cassie_follow.cc](Motion_Planner/drake/CDC/src/run_cassie_follow.cc) adjust the path in `file_name = "path/drake/CDC/vis/..."` to match the path to the drake directory on your local machine. 

## Running the code
### Setting up action.json file from Task_Planner
1- Once an action.json file is generated from Task_Planner, copy and past the file into drake/CDC/vis/ .

2- In CDC/src/simualte_psp.cc adjust the path in 
`BeliefIOParser parser("path/drake/CDC/vis/actions_CDC_Sub.json");` and choose the desired action file.

### Phase-Space Planning and trajectory generation 
1- Open terminal and go to the drake folder `cd path/drake/`

2- run `CC=clang-6.0 CXX=clang++-6.0 bazel run CDC:simulate_psp`
This will generate the trajectory .txt files.

### Drake Visualization 
Make sure that the trajectories are generated before hand as shown before.
1- Open termminal and run
```
cd path/drake/
bazel-bin/tools/drake_visualizer
```
2- Open another terminal and run
```
cd path/drake/
bazel-bin/lcmtypes/drake-lcm-spy
```
3- Open a third terminal and run 
```
cd path/drake/
CC=clang-6.0 CXX=clang++-6.0 bazel run CDC:run_cassie_follow
```

### Py.plot Visualization 
1- Open terminal and run
```
cd path/drake/CDC/vis/
python vis_psp.py 
```



# Task Planner



# Publiciations 

This repo contains the code used for implementation in our published work:-
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


The Motion_Planner directory contains the code nacessary to generate the center of mass, foot trajectories as well as foot placement location using phase-space planning. It also containts a Drake visualization code of the Cassie bipedal robot following the generated trajectories in the proposed environment.
