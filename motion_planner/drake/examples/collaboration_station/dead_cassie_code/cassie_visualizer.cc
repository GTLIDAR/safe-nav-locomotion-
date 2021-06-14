#include <fstream>
#include <gflags/gflags.h>
#include <iostream>
#include <json/value.h>
#include <jsoncpp/json/json.h>
#include "drake/common/drake_assert.h"
#include "drake/common/find_resource.h"
#include "drake/examples/cassie/cassie_lcm.h"
#include "drake/geometry/geometry_visualization.h"
#include "drake/lcmt_cassie_command.hpp"
#include "drake/lcmt_cassie_status.hpp"
#include "drake/math/rigid_transform.h"
// #include "drake/multibody/tree/quaternion_floating_joint.h"
#include "drake/multibody/plant/multibody_plant.h"
#include "drake/multibody/parsing/parser.h"
// #include "systems/primitives/subvector_pass_through.h"
#include "drake/systems/analysis/simulator.h"
#include "drake/systems/analysis/simulator_gflags.h"
#include "drake/systems/framework/diagram.h"
#include "drake/systems/framework/diagram_builder.h"
#include "drake/systems/framework/leaf_system.h"
#include "drake/systems/lcm/lcm_publisher_system.h"
#include "drake/systems/lcm/lcm_subscriber_system.h"
#include "drake/systems/lcm/lcm_interface_system.h"
#include "drake/systems/primitives/constant_vector_source.h"
#include "drake/systems/primitives/demultiplexer.h"
#include "drake/systems/primitives/discrete_derivative.h"
#include "drake/systems/rendering/multibody_position_to_geometry_pose.h"
#include "json/json.h"


namespace drake {
namespace examples {
namespace collaboration_station {
namespace {

DEFINE_bool(floating_base, true, "Fixed or floating base model");
DEFINE_bool(com, true, "Visualize the COM as a sphere");
DEFINE_bool(com_ground, true,
    "If com=true, sets whether the COM should be shown on the ground (z=0)"
    " or at the correct height.");
DEFINE_string(channel, "CASSIE_STATE_DISPATCHER",
              "LCM channel for receiving state. "
              "Use CASSIE_STATE_SIMULATION to get state from simulator, and "
              "use CASSIE_STATE_DISPATCHER to get state from state estimator");
DEFINE_double(sim_dt, 3e-3,
              "The time step to use for MultibodyPlant model "
              "discretization.");
DEFINE_string(config_file, "/home/yuki/drake/examples/collaboration_station/config.json", 
              "config file name");

// DEFINE_bool(debug_mode, true, "debug mode");

// using dairlib::systems::SubvectorPassThrough;
using drake::geometry::SceneGraph;
using drake::multibody::MultibodyPlant;
using drake::multibody::RigidBody;
// using drake::multibody::SpatialInertia;
// using drake::geometry::Sphere;
// using drake::multibody::UnitInertia;
using drake::math::RigidTransform;
using drake::math::RigidTransformd;
using systems::Demultiplexer;
using drake::manipulation::cassie::CassieStatusReceiver;
using drake::manipulation::cassie::CassieStatusSender;
using drake::manipulation::cassie::kCassieLcmStatusPeriod;
using drake::systems::rendering::MultibodyPositionToGeometryPose;
using systems::StateInterpolatorWithDiscreteDerivative;
using drake::systems::Simulator;
using Eigen::VectorXd;
using Eigen::Vector3d;
using std::endl;
using std::cout;
using Eigen::Translation3d;
using math::RollPitchYaw;
// using multibody::QuaternionFloatingJoint;

void json_parser(){
  Json::Reader reader;
  Json::Value root;  
  cout << "json parser activated." << endl;
  
  // User does not have to specify /home/your_name/ anymore!
  std::ifstream myfile(FindResourceOrThrow("drake/examples/"
                        "collaboration_station/config.json"));
  myfile >> root;
  cout << "reading json config file completed." << endl;

  // Example of accessing (DO NOT ERASE BELOW)
  // cout << root["name"].asString() << endl;
}


int do_main(int argc, char* argv[]) {

  // Load config.json file first
  Json::Reader reader;
  Json::Value root;
  cout << "json parser activated." << endl;
  
  // User does not have to specify /home/your_name/ anymore!
  std::ifstream myfile(FindResourceOrThrow("drake/examples/"
                        "collaboration_station/config.json"));
  myfile >> root;
  cout << "reading json config file completed." << endl;


  gflags::ParseCommandLineFlags(&argc, &argv, true);

  drake::systems::DiagramBuilder<double> builder;

  // Comment to self:
  //  You cannot use this for visualization!!!
  // auto [plant, scene_graph] =
  //   multibody::AddMultibodyPlantSceneGraph(&builder, 0.0);

  MultibodyPlant<double> plant(1e-5);
  plant.set_name("plant");

  SceneGraph<double>& scene_graph = *builder.AddSystem<SceneGraph>();
  scene_graph.set_name("scene_graph");

  // This function MUST be called before AddModelFromFile
  plant.RegisterAsSourceForSceneGraph(&scene_graph);

  multibody::Parser parser(&plant, &scene_graph);

  // Load Environment
  multibody::ModelInstanceIndex home_instance = parser.AddModelFromFile(
    FindResourceOrThrow(root["environment_urdf"].asString()));
  // Load Environment floor 2
  multibody::ModelInstanceIndex floor_2_instance = parser.AddModelFromFile(
    FindResourceOrThrow(root["floor_2_urdf"].asString()));
  // Load Stairs
  multibody::ModelInstanceIndex stairs_instance = parser.AddModelFromFile(
    FindResourceOrThrow(root["stairs_urdf"].asString()));
  // Load Cupboard
  multibody::ModelInstanceIndex cupboard_instance = parser.AddModelFromFile(
    FindResourceOrThrow(root["cupboard_rigid_urdf"].asString()));
  // Load Cassie    
  multibody::ModelInstanceIndex cassie_instance = parser.AddModelFromFile(
    FindResourceOrThrow(root["cassie_urdf"].asString()));
  // Load Kuka
  multibody::ModelInstanceIndex iiwa_instance = parser.AddModelFromFile(
    FindResourceOrThrow(root["iiwa_urdf"].asString()));
  // Load WSG                                              
  multibody::ModelInstanceIndex wsg_instance = parser.AddModelFromFile(
    FindResourceOrThrow(root["wsg_urdf"].asString()));
  // Load Quadrotor1
  multibody::ModelInstanceIndex drone_instance = parser.AddModelFromFile(
    FindResourceOrThrow(root["drone_1_urdf"].asString()));
  // Load Quadrotor2
  multibody::ModelInstanceIndex drone_instance2 = parser.AddModelFromFile(
    FindResourceOrThrow(root["drone_2_urdf"].asString()));
  // Load Turtlebot
  multibody::ModelInstanceIndex turtle_instance = parser.AddModelFromFile(
    FindResourceOrThrow(root["turtle_1_urdf"].asString()));
  // Load Turtlebot2
  multibody::ModelInstanceIndex turtle_instance2 = parser.AddModelFromFile(
    FindResourceOrThrow(root["turtle_2_urdf"].asString()));


  // Weld environment
  const RigidTransform<double> X_WT(
      Vector3d(0, 0, 0));
  plant.WeldFrames(plant.world_frame(), plant.GetFrameByName(
      "floor", home_instance), X_WT);

  // Weld environment
  plant.WeldFrames(plant.world_frame(), plant.GetFrameByName(
      "center", floor_2_instance), X_WT);

  // Weld environment
  const RigidTransform<double> X_WS(
      AngleAxis<double>(M_PI/2, Vector3<double>::UnitZ()), Vector3d(-1, -3, -0.05));
  plant.WeldFrames(plant.world_frame(), plant.GetFrameByName(
      "step_0", stairs_instance), X_WS);

  // Weld environment
  const RigidTransform<double> X_Wcup(
      RollPitchYaw<double>(0, 0, M_PI), Vector3d(3.25, 0.5, 0.5));
  plant.WeldFrames(plant.world_frame(), plant.GetFrameByName(
      "cupboard_body", cupboard_instance), X_Wcup);

  // Don't weld Cassie to the ground!! 
  // TODO: Comment this code out and fix the cassie-dissappearance bug
  // Weld Cassie for the picture (smile!!)
  const RigidTransform<double> X_WTT(
      AngleAxis<double>(-M_PI/2, Vector3<double>::UnitZ()), Vector3d(0, 0, 0.95));
  plant.WeldFrames(plant.world_frame(), plant.GetFrameByName(
      "pelvis", cassie_instance), X_WTT);

  // Weld iiwa
  const RigidTransform<double> X_WI(
      RollPitchYaw<double>(0, 0, M_PI), Vector3d(2, 0.5, 0.3));
  plant.WeldFrames(plant.world_frame(), plant.GetFrameByName(
      "iiwa_link_0", iiwa_instance), X_WI);

  //For wsg
  const multibody::Frame<double>& link7 =
      plant.GetFrameByName("iiwa_link_7", iiwa_instance);

  // Weld WSG
  const RigidTransform<double> X_7G(
      RollPitchYaw<double>(M_PI_2, 0, M_PI_2), Vector3d(0, 0, 0.114));
  plant.WeldFrames(link7, plant.GetFrameByName(
      "body", wsg_instance), X_7G);

  // Weld drone1
  const RigidTransform<double> drone_1(
      Vector3d(2.5, 0, 1.7));
  plant.WeldFrames(plant.world_frame(), plant.GetFrameByName(
      "base_link", drone_instance), drone_1);
  
  // Weld drone2
  const RigidTransform<double> drone_2(
      Vector3d(-1.5, -1.5, 1.6));
  plant.WeldFrames(plant.world_frame(), plant.GetFrameByName(
      "base_link", drone_instance2), drone_2);

  // Weld turtle
  const RigidTransform<double> turtle_1(
      Vector3d(-1.5, -1.5, 0.1));
  plant.WeldFrames(plant.world_frame(), plant.GetFrameByName(
      "base_footprint", turtle_instance), turtle_1);

  // Weld turtle2
  const RigidTransform<double> turtle_2(
      Vector3d(0, 0, 0));
  plant.WeldFrames(plant.world_frame(), plant.GetFrameByName(
      "base_footprint", turtle_instance2), turtle_2);

    // const QuaternionFloatingJoint<double>& cassie_world_joint =
    //   plant.AddJoint<QuaternionFloatingJoint>("cassie_to_world_joint",
    //             plant.world_body(), std::nullopt,
    //             plant.GetFrameByName("pelvis", cassie_instance),std::nullopt,
    //             X_WTT
    //   );

  // This doesn't matter for visualization
  // plant.mutable_gravity_field().set_gravity_vector(-9.81 * Vector3d::UnitZ());
  plant.Finalize();

  // Get number of joints
  const int num_joints = plant.num_positions(cassie_instance);
  drake::log()->info("\nnum_pos: {}\nnum_vels: {}\nnum_dof: {}\nnum_mbp_sts: {}\nnum_acts: {}"
                      "\nnum_joints: {}\nnum_bodies: {}",
                      num_joints, plant.num_velocities(cassie_instance), plant.num_actuated_dofs(cassie_instance),
                      plant.num_multibody_states(), plant.num_actuators(),plant.num_joints(), plant.num_bodies());
  // From urdf:
  // 21 links
  // 4 fixed and 16 revolute joints = 20
  // 10 motors

  // From logger
  // 21 links/pos
  // 20 vel
  // total of 41 mbp states

  // Create all systems
  auto lcm = builder.AddSystem<drake::systems::lcm::LcmInterfaceSystem>();

  auto state_sub = builder.AddSystem(
      systems::lcm::LcmSubscriberSystem::Make<drake::lcmt_cassie_status>(
          "CASSIE_STATUS", lcm));
  state_sub->set_name("state_subscriber");

  auto state_receiver =
      builder.AddSystem<CassieStatusReceiver>(num_joints);
  state_receiver->set_name("state_receiver");

  // auto passthrough = builder.AddSystem<SubvectorPassThrough>(
  //   state_receiver->get_output_port(0).size(), 0, plant.num_positions());
  // passthrough->set_name("passthrough");

  auto to_pose =
      builder.AddSystem<MultibodyPositionToGeometryPose<double>>(plant);
  to_pose->set_name("to_pose");

  auto status_pub = builder.AddSystem(
      systems::lcm::LcmPublisherSystem::Make<lcmt_cassie_status>(
          "CASSIE_GARBAGE", lcm, kCassieLcmStatusPeriod /* publish period */));
  status_pub->set_name("status_publisher");

  auto status_sender = builder.AddSystem<CassieStatusSender>(num_joints);
  status_sender->set_name("status_sender");

  VectorX<double> constant_vector = VectorX<double>::Zero(num_joints);
    
  auto constant_zero_source =
    builder.AddSystem<systems::ConstantVectorSource<double>>(
                                                      constant_vector);
  constant_zero_source->set_name("zero input");

  // Connect all systems
  builder.Connect(state_sub->get_output_port(),
                  state_receiver->get_input_port());
  // builder.Connect(state_receiver->get_position_measured_output_port(),
  //                 passthrough->get_input_port());
  // builder.Connect(passthrough->get_output_port(),
  //                 to_pose->get_input_port());
  builder.Connect(state_receiver->get_position_measured_output_port(),
                  to_pose->get_input_port());
  builder.Connect(to_pose->get_output_port(), 
                  scene_graph.get_source_pose_port(plant.get_source_id().value()));


  builder.Connect(constant_zero_source->get_output_port(),
                  status_sender->get_position_measured_input_port());
  builder.Connect(constant_zero_source->get_output_port(),
                  status_sender->get_velocity_estimated_input_port());
  builder.Connect(constant_zero_source->get_output_port(),
                  status_sender->get_position_commanded_input_port());
  builder.Connect(constant_zero_source->get_output_port(),
                  status_sender->get_torque_commanded_input_port());
  builder.Connect(constant_zero_source->get_output_port(),
                  status_sender->get_torque_measured_input_port());
  builder.Connect(constant_zero_source->get_output_port(),
                  status_sender->get_torque_external_input_port());
  builder.Connect(status_sender->get_output_port(),
                  status_pub->get_input_port());
  drake::geometry::ConnectDrakeVisualizer(&builder, scene_graph, lcm);

  // drake::log()->info("cassie_inst: {}", cassie_instance);
  // drake::log()->info("home_inst: {}", home_instance);

  std::unique_ptr<systems::Diagram<double>> diagram = builder.Build();
  std::unique_ptr<systems::Context<double>> diagram_context =
      diagram->CreateDefaultContext();

  // SetDefaultState(*diagram_context, &diagram_context->get_mutable_state());





  // diagram->SetDefaultContext(diagram_context.get());

      // drake::log()->info("yes0");

/*
  state_receiver->set_initial_position(
      &diagram->GetMutableSubsystemContext(*state_receiver,
                                           diagram_context.get()),
      VectorX<double>::Zero(plant.num_actuators()));

  // systems::Context<double>& pose_context =
  //     diagram->GetMutableSubsystemContext(*scene_graph, &diagram_context);

  // const auto& sg_context = 
  //     diagram->GetMutableSubsystemContext(scene_graph, &diagram_context);

  // auto state_value =
  //     diagram_context->get_mutable_discrete_state(0).get_mutable_value();
  // state_value.head(num_joints) = VectorX<double>::Zero(num_joints);


  // const drake::multibody::Body<double>& pelvis = plant.GetBodyByName("pelvis");
  //     drake::log()->info("yes1");

  // systems::Context<double>& plant_context =
  //     diagram->GetMutableSubsystemContext(plant, diagram_context.get());

  //     drake::log()->info("yes2");

  // const Translation3d X_WP(0.0, 0.0, 0.95);
  // plant.SetFreeBodyPoseInWorldFrame(&sg_context, pelvis, X_WP);
  //     drake::log()->info("yes3");

  // Set cassie as free body
  // systems::Context<double>& plant_context =
  //     diagram->GetMutableSubsystemContext(plant, diagram_context.get());

  // Context<double>& plant_context =
  //     GetMutableSubsystemContext(*plant_, context);
  // ContinuousState<double>& plant_state =
  //     plant_context.get_mutable_continuous_state();

  // auto& context = simulator.get_mutable_context();

  // const auto& sg_context = 
  //     diagram->GetMutableSubsystemContext(scene_graph, &context);
// systems::Context<double>& plant_context =
//       diagram->GetMutableSubsystemContext(plant, diagram_context.get());
*/


  // RigidTransform<double> X_WTT(AngleAxis<double>(-M_PI/2, Vector3<double>::UnitZ()),
  //                     Vector3d(0, 0, 0.95));

  // systems::Context<double>& state_receiver_context = 
  //     diagram->GetMutableSubsystemContext(*state_receiver, diagram_context.get());
        // drake::log()->info("got it");
        // plant.SetFreeBodyPoseInWorldFrame(&state_receiver_context, plant.GetBodyByName("pelvis"),
        //                                   X_WTT);
        // drake::log()->info("got it2 ");

  // plant.SetFreeBodyPose(&state_receiver_context,  plant.GetBodyByName("pelvis"), X_WTT);

  /// Use the simulator to drive at a fixed rate
  /// If set_publish_every_time_step is true, this publishes twice
  /// Set realtime rate. Otherwise, runs as fast as possible  
  systems::Simulator<double> simulator(*diagram, std::move(diagram_context));
  systems::Context<double>& root_context = simulator.get_mutable_context();

  // Context: 3 abs, 0 cont, 0 dis
  drake::log()->info("context absStates: {}",root_context.num_abstract_states());
  drake::log()->info("context contStates: {}",root_context.num_continuous_states());
  drake::log()->info("context disStates: {}",root_context.num_discrete_state_groups());

  state_receiver->set_initial_position(
      &diagram->GetMutableSubsystemContext(*state_receiver, &root_context),
      VectorX<double>::Zero(3));

  // BasicVector<T>& state_vector = dynamic_cast<BasicVector<T>&>(
  //     context_->get_mutable_continuous_state_vector());
  // state_vector.set_value(values.x0.value());



  simulator.Initialize();
  simulator.set_publish_every_time_step(false);
  simulator.set_publish_at_initialization(false);
  simulator.set_target_realtime_rate(1.0);
  drake::log()->info("visualizer started");


// const auto& sg_context = 
  //     diagram->GetMutableSubsystemContext(scene_graph, &diagram_context);

// const auto& state_receiver_context = diagram->GetMutableSubsystemContext(*state_receiver,
//                                            &simulator.get_mutable_context());


//   state_receiver->set_initial_position(state_receiver_context,
//       VectorX<double>::Zero(plant.num_actuators()));


  simulator.AdvanceTo(std::numeric_limits<double>::infinity());


  return 0;
}

} // namespace no-dependent-files
} // namespace collaboration_station
} // namespace examples
} // namespace drake

int main(int argc, char* argv[]) {
  return drake::examples::collaboration_station::do_main(argc, argv);
}