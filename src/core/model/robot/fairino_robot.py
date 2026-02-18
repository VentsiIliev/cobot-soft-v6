import platform
import logging
from typing import List

import requests

from modules.utils.custom_logging import setup_logger, LoggerContext, log_info_message, log_error_message, \
    log_debug_message
from core.model.robot.IRobot import IRobot
from core.model.robot.enums.axis import Direction
from frontend.core.services.domain.RobotService import RobotAxis

if platform.system() == "Windows":
    pass

elif platform.system() == "Linux":
    logging.info("Linux detected")
    from libs.fairino.linux.fairino import Robot
else:
    raise Exception("Unsupported OS")

ENABLE_LOGGING = True  # Enable or disable logging
# Initialize logger if enabled
if ENABLE_LOGGING:
    robot_logger = setup_logger("RobotWrapper")
else:
    robot_logger = None


class TestRobotWrapper(IRobot):
    """
       A full mock of the Fairino Robot interface.
       Implements every method used by FairinoRobot and returns safe dummy values.
       """

    def __init__(self):
        print("⚙️  TestRobot initialized (mock robot).")

    # --- Motion commands ---
    def move_cartesian(self, position, tool=0, user=0, vel=100, acc=30, blendR=0):
        print(f"[MOCK] MoveCart -> pos={position}, tool={tool}, user={user}, vel={vel}, acc={acc}")
        return 0

    def move_liner(self, position, tool=0, user=0, vel=100, acc=30, blendR=0):
        print(f"[MOCK] MoveL -> pos={position}, tool={tool}, user={user}, vel={vel}, acc={acc}, blendR={blendR}")
        return 0

    def start_jog(self, axis: RobotAxis, direction: Direction, step, vel, acc):
        print(f"[MOCK] StartJOG -> axis={axis}, direction={direction}, step={step}, vel={vel}, acc={acc}")
        return 0

    def stop_motion(self):
        print("[MOCK] StopMotion called")
        return 0

    def ResetAllError(self):
        print("[MOCK] ResetAllError called")
        return 0

    def execute_path(self,path,rx,ry,rz,vel,acc,blocking):
        print(f"[FairinoRobot] execute_path called with path: {path}")

    # --- State queries ---
    def GetActualTCPPose(self):
        # print("[MOCK] GetActualTCPPose called")
        # Returning tuple to match expected structure (status, pose)
        return (0, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def get_current_position(self):
        # print("[MOCK] GetActualTCPPose called")
        # Returning tuple to match expected structure (status, pose)
        return (0, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def get_current_velocity(self):
        print("[MOCK] GetActualTCPCompositeSpeed called")
        return (0, [0.0])  # mimic real return: (status, [speed])

    def GetSDKVersion(self):
        print("[MOCK] GetSDKVersion called")
        return "TestRobot SDK v1.0"


class FairinoRos2Client:
    """
    HTTP client for controlling Fairino robot via ROS2 bridge.
    Implements the same interface as FairinoRobot (IRobot).

    Usage:
        # Instead of: robot = FairinoRobot(ip="192.168.1.100")
        # Use:        robot = FairinoRos2Client(server_url="http://localhost:5000")
    """

    def __init__(self, server_url="http://localhost:5000", ip=None):
        """
        Initialize the ROS2 bridge client.

        Args:
            server_url: URL of the bridge server
            ip: Robot IP (for compatibility, not used in ROS2 version)
        """
        self.server_url = server_url.rstrip('/')
        self.ip = ip or "ros2_bridge"

        # Verify connection
        health = self.health_check()
        if health.get("status") != "ok":
            raise ConnectionError(f"Could not connect to ROS2 bridge at {server_url}")

        print(f"✓ FairinoRos2Client connected to bridge at {server_url}")

    def health_check(self):
        """Check if bridge server is running"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=2)
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ============ Motion Commands ============

    def move_cartesian(self, position, tool=0, user=0, vel=30, acc=30, blendR=0):
        """
        Moves the robot in Cartesian space (point-to-point).

        Args:
            position (list): Target Cartesian position [x, y, z, rx, ry, rz]
            tool (int): Tool frame ID
            user (int): User frame ID
            vel (float): Velocity (percentage 0-100)
            acc (float): Acceleration (percentage 0-100)
            blendR (float): Blend radius (not used in ROS2 implementation)

        Returns:
            int: 0 on success, error code otherwise
        """
        try:
            payload = {
                "position": position,
                "tool": tool,
                "user": user,
                "vel": vel,
                "acc": acc
            }
            response = requests.post(f"{self.server_url}/move/cartesian", json=payload, timeout=30)
            result = response.json()
            return result.get("result", 0)
        except Exception as e:
            print(f"move_cartesian error: {e}")
            return -1

    def MoveCart(self, position, tool=0, user=0, vel=30, acc=30):
        """Alias for move_cartesian (matches original SDK)"""
        return self.move_cartesian(position, tool, user, vel, acc)

    def move_liner(self, position, tool=0, user=0, vel=30, acc=30, blendR=0):
        """
        Executes a linear movement with blending.

        Args:
            position (list): Target position [x, y, z, rx, ry, rz]
            tool (int): Tool frame ID
            user (int): User frame ID
            vel (float): Velocity (percentage 0-100)
            acc (float): Acceleration (percentage 0-100)
            blendR (float): Blend radius (not used in ROS2 implementation)

        Returns:
            int: 0 on success, error code otherwise
        """
        try:
            payload = {
                "position": position,
                "tool": tool,
                "user": user,
                "vel": vel,
                "acc": acc
            }
            response = requests.post(f"{self.server_url}/move/linear", json=payload, timeout=30)
            result = response.json()
            return result.get("result", 0)
        except Exception as e:
            print(f"move_liner error: {e}")
            return -1

    def MoveL(self, position, tool=0, user=0, vel=30, acc=30, blendR=0):
        """Alias for move_liner (matches original SDK)"""
        return self.move_liner(position, tool, user, vel, acc, blendR)

    def execute_path(self, path, rx=None, ry=None, rz=None, vel=0.6, acc=0.4, blocking=False):
        """
        Execute multi-waypoint Cartesian path.

        Args:
            path: List of waypoints [[x,y,z], ...] or [[x,y,z,rx,ry,rz], ...]
            rx, ry, rz: Orientation (if not specified in waypoints)
            vel: Velocity scaling (0.0-1.0)
            acc: Acceleration scaling (0.0-1.0)
            blocking: Wait for completion

        Returns:
            int: 0 on success, -1 on error
        """
        try:
            payload = {
                "path": path,
                "rx": rx,
                "ry": ry,
                "rz": rz,
                "vel": vel,
                "acc": acc,
                "blocking": blocking
            }
            response = requests.post(f"{self.server_url}/execute/path", json=payload, timeout=120)
            result = response.json()
            return result.get("result", 0)
        except Exception as e:
            print(f"execute_path error: {e}")
            return -1

    def start_jog(self, axis, direction, step, vel, acc):
        """
        Starts jogging the robot in a specified axis and direction.

        Args:
            axis (Axis or int): Axis to jog (0=X, 1=Y, 2=Z or Axis enum)
            direction (Direction or int): Jog direction (1=PLUS, -1=MINUS or Direction enum)
            step (float): Distance to move (mm)
            vel (float): Velocity of jog (percentage 0-100)
            acc (float): Acceleration of jog (percentage 0-100)

        Returns:
            int: 0 on success, -1 on error
        """
        try:
            # Handle enum types (extract .value if present)
            axis_val = axis.value if hasattr(axis, 'value') else axis
            dir_val = direction.value if hasattr(direction, 'value') else direction

            payload = {
                "axis": axis_val,
                "direction": dir_val,
                "step": step,
                "vel": vel,
                "acc": acc
            }
            response = requests.post(f"{self.server_url}/jog", json=payload, timeout=10)
            result = response.json()
            return result.get("result", 0)
        except Exception as e:
            print(f"start_jog error: {e}")
            return -1

    def StartJOG(self, ref=4, nb=0, dir=1, vel=10, acc=10, max_dis=10):
        """
        Alias for start_jog (matches original SDK).

        Args:
            ref: Reference frame (not used in ROS2)
            nb: Axis number (0=X, 1=Y, 2=Z)
            dir: Direction (1=positive, -1=negative)
            vel: Velocity
            acc: Acceleration
            max_dis: Maximum distance (step)
        """
        return self.start_jog(nb, dir, max_dis, vel, acc)

    def stop_motion(self):
        """
        Stops all current robot motion.

        Returns:
            int: 0 on success, -1 on error
        """
        try:
            response = requests.post(f"{self.server_url}/stop", timeout=5)
            result = response.json()
            return 0 if result.get("success") else -1
        except Exception as e:
            print(f"stop_motion error: {e}")
            return -1

    def StopMotion(self):
        """Alias for stop_motion (matches original SDK)"""
        return self.stop_motion()

    # ============ State Queries ============

    def get_current_position(self):
        """
        Retrieves the current TCP (tool center point) position.

        Returns:
            list: Current robot TCP pose [x, y, z, rx, ry, rz] or None on error
        """
        try:
            response = requests.get(f"{self.server_url}/position/current", timeout=2)
            data = response.json()
            position = data.get("position")

            # Match FairinoRobot behavior: return None if error
            if position is None or isinstance(position, int):
                return None
            return position
        except Exception as e:
            print(f"get_current_position error: {e}")
            return None

    def GetActualTCPPose(self):
        """
        Get actual TCP pose (matches original SDK format).

        Returns:
            tuple: (status, [x, y, z, rx, ry, rz])
        """
        position = self.get_current_position()
        if position is None:
            return (-1, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        return (0, position)

    def get_current_velocity(self):
        """
        Retrieves the current Cartesian velocity.

        Returns:
            tuple: (status, [vx, vy, vz]) or None on error
        """
        try:
            response = requests.get(f"{self.server_url}/velocity/current", timeout=2)
            data = response.json()
            velocity = data.get("velocity")

            if velocity is None:
                return None
            return (0, velocity)
        except Exception as e:
            print(f"get_current_velocity error: {e}")
            return None

    def GetActualTCPCompositeSpeed(self):
        """
        Get composite TCP speed (matches original SDK).

        Returns:
            tuple: (status, [speed])
        """
        vel = self.get_current_velocity()
        if vel is None:
            return (0, [0.0])
        # Calculate magnitude
        import math
        magnitude = math.sqrt(sum(v**2 for v in vel[1]))
        return (0, [magnitude])

    def get_current_acceleration(self):
        """
        Retrieves the current Cartesian acceleration.

        Note: Not implemented in base bridge, returns None
        """
        return None

    # ============ Configuration & Control ============

    def enable(self):
        """
        Enables the robot, allowing motion.
        Note: In ROS2 implementation, robot is always enabled when node is active.
        """
        print("Robot enable called (ROS2 robot is always enabled)")
        return 0

    def RobotEnable(self, state):
        """Alias for enable/disable (matches original SDK)"""
        if state == 1:
            return self.enable()
        else:
            return self.disable()

    def disable(self):
        """
        Disables the robot, preventing motion.
        Note: In ROS2 implementation, use stop_motion() instead.
        """
        print("Robot disable called (use stop_motion for ROS2)")
        return 0

    def printSdkVersion(self):
        """
        Prints the current SDK version.

        Returns:
            str: SDK version string
        """
        version = "FairinoRos2Client v1.0 (ROS2 Bridge)"
        print(version)
        return version

    def GetSDKVersion(self):
        """Alias for printSdkVersion (matches original SDK)"""
        return "ROS2 Fairino Robot Controller v1.0"

    def setDigitalOutput(self, portId, value):
        """
        Sets a digital output pin on the robot.

        Args:
            portId (int): Output port number
            value (int): Value to set (0 or 1)

        Returns:
            int: 0 on success, -1 on error

        Note: Not implemented in the ROS2 version - requires hardware interface
        """
        print(f"setDigitalOutput: port {portId} -> {value} (not implemented in ROS2)")
        return -1

    def SetDO(self, portId, value):
        """Alias for setDigitalOutput (matches original SDK)"""
        return self.setDigitalOutput(portId, value)

    def resetAllErrors(self):
        """
        Resets all current error states on the robot.

        Returns:
            int: 0 on success, -1 on error

        Note: Not applicable in ROS2 version
        """
        print("resetAllErrors called (not applicable in ROS2)")
        return 0

    def ResetAllError(self):
        """Alias for resetAllErrors (matches original SDK)"""
        return self.resetAllErrors()

    # ============ WorkObject Support ============

    def set_workobject(self, origin, user_id=0):
        """
        Set work object coordinate frame.

        Args:
            origin: [x_mm, y_mm, z_mm, rx_deg, ry_deg, rz_deg]
            user_id: User frame ID (default 0)

        Returns:
            int: 0 on success, -1 on error
        """
        try:
            payload = {
                "origin": origin,
                "user_id": user_id
            }
            response = requests.post(f"{self.server_url}/workobject/set", json=payload, timeout=5)
            result = response.json()
            return 0 if result.get("success") else -1
        except Exception as e:
            print(f"set_workobject error: {e}")
            return -1

class FairinoRobot(IRobot):
    """
      A wrapper for the real robot controller, abstracting motion and I/O operations.
      """

    def __init__(self, ip):
        """
               Initializes the robot wrapper and connects to the robot via RPC.

               Args:
                   ip (str): IP address of the robot controller.
               """
        self.ip = ip
        # self.robot = Robot.RPC(self.ip)  # Real robot - use in production
        self.robot = TestRobotWrapper()  # For testing purposes, replace it with a real robot in production
        # self.robot= FairinoRos2Client()
        self.logger_context = LoggerContext(logger=robot_logger, enabled=ENABLE_LOGGING)
        if self.robot is not None:
            log_info_message(self.logger_context, f"RobotWrapper initialized for robot at {self.ip}")
        else:
            log_error_message(self.logger_context, f"Failed to connect to robot at {self.ip}")
            raise ConnectionError(f"Could not connect to robot at {self.ip}")

        """overSpeedStrategy: over speed handling strategy
        0 - strategy off;
        1 - standard;
        2 - stop on error when over speeding;
        3 - adaptive speed reduction, default 0"""
        self.overSpeedStrategy = 3



    def move_cartesian(self, position, tool=0, user=0, vel=30, acc=30, blendR=0):
        """
              Moves the robot in Cartesian space.

              Args:
                  blendR
                  position (list): Target Cartesian position.
                  tool (int): Tool frame ID.
                  user (int): User frame ID.
                  vel (float): Velocity.
                  acc (float): Acceleration.

              Returns:
                  list: Result from robot move command.
              """

        result = self.robot.MoveCart(position, tool, user, vel=vel, acc=acc)
        log_debug_message(self.logger_context,
                          f"MoveCart to {position} with tool {tool}, user {user}, vel {vel}, acc {acc} -> result: {result}")
        return result

    def move_liner(self, position, tool=0, user=0, vel=30, acc=30, blendR=0):
        """
              Executes a linear movement with blending.

              Args:
                  position (list): Target position.
                  tool (int): Tool frame ID.
                  user (int): User frame ID.
                  vel (float): Velocity.
                  acc (float): Acceleration.
                  blendR (float): Blend radius.

              Returns:
                  list: Result from robot linear move command.
              """

        result = self.robot.MoveL(position, tool, user, vel=vel, acc=acc, blendR=blendR)
        log_debug_message(self.logger_context,
                          f"MoveL to {position} with tool {tool}, user {user}, vel {vel}, acc {acc}, blendR {blendR} -> result: {result}")
        return result

    def execute_trajectory(self, path,rx=180,ry=0,rz=0,vel=0.1,acc=0.1,blocking=False):
        print(f"[FairinoRobot] execute_trajectory called with path: {path}")
        self.robot.execute_path(path,rx=180,ry=0,rz=0,vel=vel,acc=acc,blocking=blocking)

    def get_current_position(self):
        """
              Retrieves the current TCP (tool center point) position.

              Returns:
                  list: Current robot TCP pose.
              """
        try:
            currentPose = self.robot.GetActualTCPPose()
        except Exception as e:
            log_error_message(self.logger_context, f"get_current_position failed: {e}")
            return None
        # print(f"GetCurrentPosition raw -> {currentPose}")
        # check if int
        if isinstance(currentPose, int):
            currentPose = None
        else:
            currentPose = currentPose[1]
        # log_debug_message(self.logger_context, f"GetCurrentPosition -> {currentPose}")
        return currentPose

    def get_current_velocity(self):
        pass

    def get_current_acceleration(self):
        pass

    def enable(self):
        """
               Enables the robot, allowing motion.
               """
        self.robot.RobotEnable(1)

    def disable(self):
        """
             Disables the robot, preventing motion.
             """
        self.robot.RobotEnable(0)

    def printSdkVersion(self):
        """
              Prints the current SDK version of the robot controller.
              """
        version = self.robot.GetSDKVersion()
        print(version)
        return version

    def setDigitalOutput(self, portId, value):
        """
              Sets a digital output pin on the robot.

              Args:
                  portId (int): Output port number.
                  value (int): Value to set (0 or 1).
              """
        result = self.robot.SetDO(portId, value)
        log_debug_message(self.logger_context, f"SetDigitalOutput port {portId} to {value} -> result: {result}")
        return result

    def start_jog(self, axis, direction, step, vel, acc):
        """
              Starts jogging the robot in a specified axis and direction.

              Args:
                  axis (Axis): Axis to jog.
                  direction (Direction): Jog direction (PLUS or MINUS).
                  step (float): Distance to move.
                  vel (float): Velocity of jog.
                  acc (float): Acceleration of jog.

              Returns:
                  object: Result of the StartJOG command.
              """
        axis = axis.value
        direction = direction.value

        result = self.robot.StartJOG(ref=4, nb=axis, dir=direction, vel=vel, acc=acc, max_dis=step)
        log_debug_message(self.logger_context,
                          f"StartJog axis {axis} direction {direction} step {step} vel {vel} acc {acc} -> result: {result}")
        return result

    def stop_motion(self):
        """
               Stops all current robot motion.

               Returns:
                   object: Result of StopMotion command.
               """
        return self.robot.StopMotion()

    def resetAllErrors(self):
        """
               Resets all current error states on the robot.

               Returns:
                   object: Result of ResetAllError command.
               """
        print(f"RobotWrapper: ResetAllError called")
        return self.robot.ResetAllError()
