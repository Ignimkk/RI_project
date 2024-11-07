# from launch import LaunchDescription
# from launch.actions import IncludeLaunchDescription
# from launch.launch_description_sources import PythonLaunchDescriptionSource
# from launch_ros.actions import Node
# from launch.substitutions import Command, PathJoinSubstitution
# from launch_ros.substitutions import FindPackageShare

# import os

# def generate_launch_description():
#     # Path to the robot URDF file
#     ribot_urdf = PathJoinSubstitution(
#         [FindPackageShare("ribot_description"), "urdf", "ribot_gazebo.urdf"]
#     )

#     # Path to the Gazebo world file
#     world_file = PathJoinSubstitution(
#         [FindPackageShare("ribot_gazebo"), "worlds", "my_world.world"]
#     )

#     # Launch Gazebo with the world
#     gazebo = IncludeLaunchDescription(
#         PythonLaunchDescriptionSource([
#             PathJoinSubstitution([FindPackageShare('gazebo_ros'), 'launch', 'gazebo.launch.py'])
#         ]),
#         launch_arguments={'world': world_file}.items(),
#     )

#     # Spawn the robot in Gazebo
#     spawn_robot = Node(
#         package='gazebo_ros',
#         executable='spawn_entity.py',
#         arguments=['-entity', 'ribot', '-file', ribot_urdf, '-x', '0', '-y', '0', '-z', '1'],
#         output='screen'
#     )

#     return LaunchDescription([
#         gazebo,
#         spawn_robot,
#     ])

###############

# from launch import LaunchDescription
# from launch.actions import IncludeLaunchDescription, TimerAction
# from launch.launch_description_sources import PythonLaunchDescriptionSource
# from launch_ros.actions import Node
# from launch.substitutions import PathJoinSubstitution
# from launch_ros.substitutions import FindPackageShare

# def generate_launch_description():
#     ribot_urdf = PathJoinSubstitution(
#         [FindPackageShare("ribot_description"), "urdf", "ribot_gazebo.urdf"]
#     )
#     world_file = PathJoinSubstitution(
#         [FindPackageShare('gazebo_ros'), 'worlds', 'empty.world']
#     )


#     gazebo = IncludeLaunchDescription(
#         PythonLaunchDescriptionSource([
#             PathJoinSubstitution([FindPackageShare('gazebo_ros'), 'launch', 'gazebo.launch.py'])
#         ]),
#         launch_arguments={'world': world_file, 'verbose': 'true'}.items(),
#     )

#     spawn_robot = Node(
#         package='gazebo_ros',
#         executable='spawn_entity.py',
#         arguments=['-entity', 'ribot', '-file', ribot_urdf, '-x', '0', '-y', '0', '-z', '1'],
#         output='log'  # Change from 'screen' to 'log' to save logs
#     )


#     # Delay spawning to ensure Gazebo is ready
#     delayed_spawn = TimerAction(
#         period=10.0,
#         actions=[spawn_robot]
#     )

#     return LaunchDescription([
#         gazebo,
#         delayed_spawn
#     ])

###############################3
import os
from os import environ
from os import pathsep
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, RegisterEventHandler, SetEnvironmentVariable
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration, EnvironmentVariable
from ament_index_python.packages import get_package_share_directory
from pathlib import Path

def generate_launch_description():
    robot_name = DeclareLaunchArgument("robot_name", default_value="ribot")
    world_name = DeclareLaunchArgument("world_name", default_value="empty.world")

    environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'
    gz_resource_path = SetEnvironmentVariable(name='GAZEBO_MODEL_PATH', value=[
        EnvironmentVariable('GAZEBO_MODEL_PATH', default_value=''),
        '/usr/share/gazebo-11/models/:',
        str(Path(get_package_share_directory('ribot_description')).parent.resolve()),
        ':',
        str(Path(get_package_share_directory('ribot_gazebo')).parent.resolve()) + "/ribot_gazebo/models",
    ])

    gz_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            FindPackageShare('gazebo_ros'),
            '/launch/gzserver.launch.py'
        ]),
        launch_arguments={
            "verbose": "true",
            "physics": "ode",
            "lockstep": "true",
            "world": PathJoinSubstitution([
                FindPackageShare('ribot_gazebo'),
                'worlds',
                LaunchConfiguration('world_name'),
            ])
        }.items(),
    )

    gz_client = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            FindPackageShare('gazebo_ros'),
            '/launch/gzclient.launch.py'
        ]),
    )

    # upload_robot = Node(
    #     package='robot_state_publisher',
    #     executable='robot_state_publisher',
    #     name='robot_state_publisher',
    #     output='screen',
    #     parameters=[{
    #         'use_sim_time': True,
    #         'robot_description': PathJoinSubstitution([
    #             FindPackageShare('ribot_description'),
    #             'urdf',
    #             'ribot_gazebo.urdf'
    #         ])
    #     }]
    # )
    
    with open('/home/mk/Projects/RI_Project/test_ws/src/ribot_description/urdf/ribot_gazebo.urdf', 'r') as urdf_file:
        robot_description = urdf_file.read()

    upload_robot = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'robot_description': robot_description
        }]
    )
    
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_robot',
        output='screen',
        arguments=[
            '-entity', LaunchConfiguration('robot_name'),
            '-topic', '/robot_description',
            '-x', LaunchConfiguration('x_pose', default='0.0'),
            '-y', LaunchConfiguration('y_pose', default='0.0'),
            '-z', '0.0',
            '-Y', LaunchConfiguration('yaw', default='0.0')
        ],
        parameters=[{
            "use_sim_time": True
        }],
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "controller_manager"]
    )

    robot_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["base_controller", "--controller-manager", "controller_manager"]
    )

    return LaunchDescription([
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_robot,
                on_exit=[joint_state_broadcaster_spawner],
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=joint_state_broadcaster_spawner,
                on_exit=[robot_controller_spawner],
            )
        ),
        gz_resource_path,
        robot_name,
        world_name,
        gz_server,
        gz_client,
        upload_robot,
        spawn_robot,
    ])
