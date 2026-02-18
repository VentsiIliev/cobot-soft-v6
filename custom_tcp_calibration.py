import numpy as np
from scipy.spatial.transform import Rotation as R
from core.model.robot import FairinoRobot


class ManualTcpCalibrator:
    def __init__(self, robot, num_points=6):
        self.robot = robot            # <-- add this
        self.num_points = num_points
        self.flange_poses = []        # List of (translation, rotation matrix)
        self.tcp_offset = None

    # ------------------------
    # Record flange pose from robot
    # ------------------------
    def record_flange_pose(self, point_index):
        """
        Retrieve the current TCP pose from the robot.
        Returns:
            t: translation vector (numpy array 3,)
            R_mat: rotation matrix (numpy array 3x3)
        """
        pose = self.robot.get_current_position()  # [x, y, z, rx, ry, rz]
        if pose is None:
            raise RuntimeError("Failed to read TCP pose from robot")

        # Translation
        t = np.array(pose[:3])

        # Convert rx, ry, rz (rpy in radians) to rotation matrix
        rpy = pose[3:]
        R_mat = R.from_euler('xyz', rpy).as_matrix()

        return t, R_mat

    # ------------------------
    # Reference point in base frame
    # ------------------------
    def get_reference_point(self):
        """
        Returns the fixed reference point coordinates in base frame.
        """
        # Optionally, take the first recorded TCP as reference
        if self.flange_poses:
            t, _ = self.flange_poses[0]
            return t
        # Or a fixed point
        return np.array([0.5, 0.2, 0.3])

    # ------------------------
    # Guide user and collect poses
    # ------------------------
    def collect_poses(self):
        print(f"\nManual TCP Calibration: {self.num_points} orientations required.")
        for i in range(self.num_points):
            input(f"\nMove the TCP to the reference point for orientation {i+1} and press ENTER when ready...")
            t, R_mat = self.record_flange_pose(i)
            self.flange_poses.append((t, R_mat))
            print(f"Pose {i+1} recorded: translation={t}, rotation matrix=\n{R_mat}")

        print("\nAll poses recorded.")

    # ------------------------
    # Compute TCP offset
    # ------------------------
    def compute_tcp(self):
        P_tip = self.get_reference_point()
        A = []
        b = []
        for t_i, R_i in self.flange_poses:
            A.append(R_i)
            b.append(P_tip - t_i)

        A = np.vstack(A)
        b = np.hstack(b)

        t_tcp, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)

        self.tcp_offset = np.zeros(6)
        self.tcp_offset[:3] = t_tcp
        self.tcp_offset[3:] = [0.0, 0.0, 0.0]  # rotation placeholder

        print("\nEstimated TCP offset relative to flange:", t_tcp)
        print("TCP offset [x, y, z, rx, ry, rz]:", self.tcp_offset)
        return self.tcp_offset

    # ------------------------
    # Full calibration
    # ------------------------
    def calibrate(self):
        self.collect_poses()
        return self.compute_tcp()


# ------------------------
# Example usage
# ------------------------
if __name__ == "__main__":
    robot_instance = FairinoRobot("192.168.58.2")  # <-- replace with your robot object
    calibrator = ManualTcpCalibrator(robot=robot_instance, num_points=4)
    tcp_offset = calibrator.calibrate()
