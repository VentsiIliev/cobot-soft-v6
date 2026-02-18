import threading
import time
from enum import Enum

import cv2
import numpy as np
import matplotlib

from core.model.robot import FairinoRobot

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


from modules.VisionSystem.VisionSystem import VisionSystem
from modules.utils.utils import applyTransformation


class PaintingAxis(Enum):
    Y = "Y"
    X = "X"

# Global variables
vision_system = VisionSystem(configFilePath="/home/ilv/cobot-soft/cobot-soft-v5.1/cobot-soft-v5/cobot-glue-dispensing-v5/src/applications/glue_dispensing_application/storage/settings/camera_settings.json",
                             storage_path="/home/ilv/cobot-soft/cobot-soft-v5.1/cobot-soft-v5/cobot-glue-dispensing-v5/src/applications/glue_dispensing_application/storage/data/calibration")
latest_frame = None
latest_contours = None
vision_running = False
capture_requested = False
frame_lock = threading.Lock()
robot = FairinoRobot("192.168.58.2")

def get_current_robot_position(robot_param):
    return robot_param.get_current_position()

def move_to_point(robot_param, point):
    tool=1
    workpiece=1
    velocity=30
    acceleration=30
    robot_param.move_cartesian(point, tool, workpiece, vel=velocity, acc=acceleration)

def vision_system_thread():
    """Background thread that continuously captures frames from vision system"""
    global latest_frame, latest_contours, vision_running, capture_requested

    print("Vision system thread started...")

    while vision_running:
        try:
            # Capture frame from vision system
            contours, frame, _ = vision_system.run()

            # Store the frame
            if frame is not None:
                with frame_lock:
                    latest_frame = frame.copy()

            # Store contours if available
            if contours is not None and len(contours) > 0:
                largestContour = contours[0]

                # If capture is requested, store the contour
                if capture_requested:
                    with frame_lock:
                        latest_contours = largestContour.copy()
                    print(f"Captured contour with {len(largestContour)} points")
                    capture_requested = False
            elif capture_requested:
                print("No contours detected!")
                capture_requested = False

            time.sleep(0.03)  # ~30 FPS

        except Exception as e:
            print(f"Error in vision thread: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(0.1)

    print("Vision system thread stopped.")


def start_vision_system():
    """Start the vision system in a background thread"""
    global vision_running, vision_thread

    vision_running = True
    vision_thread = threading.Thread(target=vision_system_thread, daemon=True)
    vision_thread.start()
    print("Vision system started in background thread")
    print("Press SPACE to capture contours from camera")
    print("Press ESC to exit")


def stop_vision_system():
    """Stop the vision system background thread"""
    global vision_running
    vision_running = False
    if 'vision_thread' in globals():
        vision_thread.join(timeout=2.0)
    print("Vision system stopped")


def get_contours_from_camera():
    """Request contour capture from vision system"""
    global capture_requested, latest_contours

    # Clear previous contours
    with frame_lock:
        latest_contours = None

    # Request new capture
    capture_requested = True

    # Wait for contours to be captured (with timeout)
    timeout = 5.0
    start_time = time.time()

    while capture_requested and (time.time() - start_time) < timeout:
        time.sleep(0.1)

    # Return the captured contours
    with frame_lock:
        if latest_contours is not None:
            return latest_contours.copy()

    return None


POINT_COLORS = {0: 'red', 1: 'blue', 2: 'green', 3: 'magenta'}


def plot_pipeline_state(ax, points, center, pivot, num_unique, title,
                        axis=PaintingAxis.Y, direction=-1):
    """Plot the current pipeline state on a matplotlib axes."""
    ax.clear()
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    # Draw contour edges
    ax.plot(xs, ys, 'k-', linewidth=1.5)
    # Draw numbered points
    for j in range(num_unique):
        color = POINT_COLORS.get(j, 'green')
        ax.plot(points[j][0], points[j][1], 'o', color=color, markersize=8)
        ax.annotate(str(j), (points[j][0], points[j][1]), textcoords="offset points",
                    xytext=(8, 8), fontsize=9, color=color, fontweight='bold')
    # Draw center
    ax.plot(center[0], center[1], 's', color='orange', markersize=8, label='center')
    # Draw pivot
    ax.plot(pivot[0], pivot[1], '^', color='lime', markersize=10, label='pivot')
    ax.set_title(title)
    ax.set_xlim(-450, 450)
    ax.set_ylim(0, 1000)
    ax.set_aspect('equal')
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.legend(loc='upper right', fontsize=7)
    ax.grid(True, alpha=0.3)


def calculate_angle_relative_to_axis(currentPoint, nextPoint, axis=PaintingAxis.Y):
    """
    Calculate the angle and length between two points relative to a given axis.

    Returns an angle such that rotating by it aligns the edge with the painting axis.
    - Y axis: arctan2(deltaX, deltaY) — rotation aligns edge with +Y
    - X axis: -arctan2(deltaY, deltaX) — rotation aligns edge with +X
    """
    print(f"In calculate_angle_relative_to_axis (axis={axis.value})")
    if np.isnan(currentPoint).any() or np.isnan(nextPoint).any():
        raise ValueError("currentPoint or nextPoint contains NaN values")

    deltaX = nextPoint[0] - currentPoint[0]
    deltaY = nextPoint[1] - currentPoint[1]
    rLength = np.sqrt(deltaX ** 2 + deltaY ** 2)

    if axis == PaintingAxis.Y:
        # Rotating by this angle aligns the edge with +Y
        rAngle = np.degrees(np.arctan2(deltaX, deltaY))
    else:
        # Rotating by this angle aligns the edge with +X
        rAngle = -np.degrees(np.arctan2(deltaY, deltaX))

    print(f"    deltaX: {deltaX}, deltaY: {deltaY}, rLength: {rLength}")

    return rAngle, rLength


def rotate_point(point, angle, pivot):
    """
    Rotates a point around a given origin by a given angle.

    :param point: The point to rotate (x, y).
    :param angle: The angle to rotate the point (in degrees).
    :param pivot: The pivot to rotate around (x, y).
    :return: The rotated point (x', y').
    """

    angle_rad = np.radians(angle)
    pivotX, pivotY = pivot
    pointX, pointY = point

    rotatedX = pivotX + np.cos(angle_rad) * (pointX - pivotX) - np.sin(angle_rad) * (pointY - pivotY)
    rotatedY = pivotY + np.sin(angle_rad) * (pointX - pivotX) + np.cos(angle_rad) * (pointY - pivotY)

    return [rotatedX, rotatedY]


def offset_point(point, offsetX, offsetY):
    """
    Offsets a point by a given offset.

    :param point: The point to offset (x, y).
    :param offsetX: The offset to apply to the point x coordinate.
    :param offsetY: The offset to apply to the point y coordinate.
    :return: The offset point (x', y').
    """
    return [point[0] + offsetX, point[1] + offsetY]


def run_pipeline(points, center, pivot, window_title, robot_param=None,
                 axis=PaintingAxis.Y, direction=-1):

    # Get current robot position for trajectory
    if robot_param is not None:
        current_pos = get_current_robot_position(robot_param)
        print(f"Current robot position: {current_pos}")
        # Extract initial values [x, y, z, rx, ry, rz]
        # Use fixed Z=400 instead of current robot Z
        initial_z = 400
        initial_rx = current_pos[3] if len(current_pos) > 3 else 180
        initial_ry = current_pos[4] if len(current_pos) > 4 else 0
        initial_rz = current_pos[5] if len(current_pos) > 5 else 0
    else:
        print("Warning: No robot parameter provided, using default values")
        initial_z = 400
        initial_rx = 180
        initial_ry = 0
        initial_rz = 0

    # Track accumulated rz rotation
    accumulated_rz = initial_rz

    # List to store trajectory points (center positions after each transformation)
    trajectory = []

    # Check if contour is closed (first == last)
    is_closed = np.array_equal(points[0], points[-1])
    num_unique_points = len(points) - 1 if is_closed else len(points)

    # Determine axis index: 0 for X, 1 for Y
    axis_idx = 0 if axis == PaintingAxis.X else 1

    print("\n" + "="*80)
    print(f"STARTING PIPELINE: {window_title}")
    print("="*80)
    print(f"Input - Points count: {len(points)} ({num_unique_points} unique, {'closed' if is_closed else 'open'})")
    print(f"Input - Center: {center}")
    print(f"Input - Pivot: {pivot}")
    print(f"Input - First point: {points[0]}")
    print(f"Input - Last point: {points[-1]}")
    print(f"Input - Contour closed: {is_closed}")
    print(f"Input - Painting axis: {axis.value}, direction: {direction}")
    print(f"Initial rz: {initial_rz}°")

    # Add initial center position to trajectory
    trajectory.append([center[0], center[1], initial_z, initial_rx, initial_ry, accumulated_rz])
    print(f"  Trajectory point 0: {trajectory[-1]}")

    # Normalize winding so shape stays on the correct side of pivot:
    #   Y painting → CW winding → shape stays LEFT of pivot
    #   X painting → CCW winding → shape stays BELOW pivot
    # Shoelace formula: positive = CW in screen coords, negative = CCW
    signed_area = 0
    for i in range(num_unique_points):
        j = (i + 1) % num_unique_points
        signed_area += points[i][0] * points[j][1] - points[j][0] * points[i][1]
    signed_area /= 2

    want_cw = (axis == PaintingAxis.Y)
    need_reverse = (signed_area < 0) if want_cw else (signed_area > 0)

    if need_reverse:
        unique = points[:num_unique_points]
        unique = [unique[0]] + unique[1:][::-1]
        points = unique + [unique[0]]
        target = "CW" if want_cw else "CCW"
        print(f"  Reversed winding to {target} (signed area was {signed_area:.1f})")
    else:
        current = "CW" if signed_area > 0 else "CCW"
        print(f"  Winding already {current} (signed area={signed_area:.1f})")

    # Setup matplotlib interactive figure
    plt.ion()
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    fig.suptitle(window_title)

    # Step 0: Draw initial state
    print("\n[STEP 0] Drawing initial shape...")
    plot_pipeline_state(ax, points, center, pivot, num_unique_points, "Step 0: Initial Shape",
                        axis=axis, direction=direction)
    plt.draw()
    plt.waitforbuttonpress()

    # Step 1: Rotate to align the first edge with the painting axis
    print(f"\n[STEP 1] Aligning first edge with {axis.value}-axis...")
    firstPoint = points[0]
    secondPoint = points[1]
    print(f"  First point: {firstPoint}")
    print(f"  Second point: {secondPoint}")

    angle, rLength = calculate_angle_relative_to_axis(firstPoint, secondPoint, axis)

    print(f"  Calculated angle relative to {axis.value}: {angle}")
    print(f"  Edge length: {rLength}")

    # No offset: aligns first edge parallel to the painting axis
    # Y: first edge becomes vertical (parallel to Y)
    # X: first edge becomes horizontal (parallel to X)

    print(f"  Rotation angle to apply: {angle}°")
    print(f"  Rotating around first point: {firstPoint}")

    # Accumulate rz rotation
    accumulated_rz += angle
    print(f"  Accumulated rz: {accumulated_rz}°")

    center = rotate_point(center, angle, firstPoint)
    print(f"  New center after rotation: {center}")

    # Add center position to trajectory after rotation
    trajectory.append([center[0], center[1], initial_z, initial_rx, initial_ry, accumulated_rz])
    print(f"  Trajectory point {len(trajectory)-1}: {trajectory[-1]}")

    for j in range(len(points)):
        points[j] = rotate_point(points[j], angle, firstPoint)

    print(f"  New first point after rotation: {points[0]}")
    print(f"  New second point after rotation: {points[1]}")

    plot_pipeline_state(ax, points, center, pivot, num_unique_points,
                        "Step 1: First Edge Aligned Horizontal", axis=axis, direction=direction)
    plt.draw()
    plt.waitforbuttonpress()

    # Step 2: Translate the first point to pivot
    print("\n[STEP 2] Translating first point to pivot...")
    xOffset = pivot[0] - firstPoint[0]
    yOffset = pivot[1] - firstPoint[1]
    print(f"  Offset to apply: X={xOffset}, Y={yOffset}")

    center = (center[0] + xOffset, center[1] + yOffset)
    print(f"  New center after translation: {center}")

    # Add center position to trajectory after translation (no rotation, rz stays same)
    trajectory.append([center[0], center[1], initial_z, initial_rx, initial_ry, accumulated_rz])
    print(f"  Trajectory point {len(trajectory)-1}: {trajectory[-1]}")

    for k in range(len(points)):
        points[k] = offset_point(points[k], xOffset, yOffset)

    print(f"  First point after translation: {points[0]}")
    print(f"  Should match pivot: {pivot}")
    print(f"  Match check: {np.allclose(points[0], pivot, atol=0.1)}")

    plot_pipeline_state(ax, points, center, pivot, num_unique_points, "Step 2: Translated to Pivot",
                        axis=axis, direction=direction)
    plt.draw()
    plt.waitforbuttonpress()

    # Step 3: Process each edge
    print("\n[STEP 3] Processing each edge...")
    for i in range(len(points) - 1):
        print(f"\n--- Processing Edge {i} -> {i+1} ---")
        print(f"  All points: {[f'[{p[0]:.1f}, {p[1]:.1f}]' for p in points]}")

        currentPoint = points[i]
        nextPoint = points[i + 1]
        print(f"  Current point ({i}): {currentPoint}")
        print(f"  Next point ({i+1}): {nextPoint}")

        angle, rLength = calculate_angle_relative_to_axis(currentPoint, nextPoint, axis)
        print(f"  Edge angle relative to {axis.value}: {angle}°")
        print(f"  Edge length: {rLength}")

        print(f"  Rotation angle: {angle}°")
        print(f"  Rotating around pivot: {pivot}")

        # Accumulate rz rotation
        accumulated_rz += angle
        print(f"  Accumulated rz: {accumulated_rz}°")

        center = rotate_point(center, angle, pivot)
        print(f"  Center after rotation: {center}")

        # Add center position to trajectory after rotation
        trajectory.append([center[0], center[1], initial_z, initial_rx, initial_ry, accumulated_rz])
        print(f"  Trajectory point {len(trajectory)-1}: {trajectory[-1]}")

        for j in range(len(points)):
            points[j] = rotate_point(points[j], angle, pivot)

        print(f"  First point after rotation: {points[0]}")
        print(f"  Second point after rotation: {points[1]}")

        plot_pipeline_state(ax, points, center, pivot, num_unique_points,
                            f"Edge {i}->{i+1}: After Rotation", axis=axis, direction=direction)
        plt.draw()
        plt.waitforbuttonpress()

        # Translate along the painting axis by edge length
        print(f"  Translating along {axis.value} by {direction} * {rLength}")
        center_list = list(center)
        center_list[axis_idx] += direction * rLength
        center = tuple(center_list)
        print(f"  Center after translation: {center}")

        # Add center position to trajectory after translation (no rotation, rz stays same)
        trajectory.append([center[0], center[1], initial_z, initial_rx, initial_ry, accumulated_rz])
        print(f"  Trajectory point {len(trajectory)-1}: {trajectory[-1]}")

        for k in range(len(points)):
            points[k][axis_idx] += direction * rLength

        print(f"  First point after translation: {points[0]}")

        plot_pipeline_state(ax, points, center, pivot, num_unique_points,
                            f"Edge {i}->{i+1}: After Translation", axis=axis, direction=direction)
        plt.draw()
        plt.waitforbuttonpress()

    print("\n" + "="*80)
    print(f"PIPELINE COMPLETED: {window_title}")
    print(f"Final center: {center}")
    print(f"Total trajectory points: {len(trajectory)}")
    print("="*80 + "\n")

    # Save trajectory to file
    import json
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"trajectory_{timestamp}.json"

    trajectory_data = {
        "timestamp": timestamp,
        "window_title": window_title,
        "painting_axis": axis.value,
        "painting_direction": direction,
        "num_points": len(trajectory),
        "pivot": pivot,
        "trajectory": trajectory
    }

    with open(filename, 'w') as f:
        json.dump(trajectory_data, f, indent=2)

    print(f"Trajectory saved to: {filename}")
    print(f"Total trajectory points saved: {len(trajectory)}")

    # Execute the trajectory step by step on space bar press
    if robot_param is not None:
        print("\n" + "="*80)
        print("TRAJECTORY EXECUTION - Step by Step")
        print("="*80)
        print("Controls:")
        print("  SPACE - Execute current trajectory point")
        print("  ESC   - Skip execution and return")
        print("="*80)

        # Create a window for key input
        cv2.namedWindow("Trajectory Execution", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Trajectory Execution", 800, 250)

        current_step = 0

        while current_step < len(trajectory):
            point = trajectory[current_step]

            # Print position to console
            print("\n" + "-"*80)
            print(f"Step {current_step + 1}/{len(trajectory)}")
            print(f"Target Position:")
            print(f"  X  = {point[0]:8.2f} mm")
            print(f"  Y  = {point[1]:8.2f} mm")
            print(f"  Z  = {point[2]:8.2f} mm")
            print(f"  RX = {point[3]:8.2f} deg")
            print(f"  RY = {point[4]:8.2f} deg")
            print(f"  RZ = {point[5]:8.2f} deg")
            print("-"*80)
            print("Press SPACE to execute this point, ESC to skip execution...")

            # Create info display window
            info_img = np.zeros((250, 800, 3), dtype=np.uint8)

            # Title
            cv2.putText(info_img, f"Step {current_step + 1}/{len(trajectory)}",
                       (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

            # Position info
            cv2.putText(info_img, f"X  = {point[0]:8.2f} mm",
                       (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(info_img, f"Y  = {point[1]:8.2f} mm",
                       (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(info_img, f"Z  = {point[2]:8.2f} mm",
                       (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            cv2.putText(info_img, f"RX = {point[3]:8.2f} deg",
                       (400, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(info_img, f"RY = {point[4]:8.2f} deg",
                       (400, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(info_img, f"RZ = {point[5]:8.2f} deg",
                       (400, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Instructions
            cv2.putText(info_img, "Press SPACE to execute",
                       (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(info_img, "Press ESC to skip",
                       (10, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            cv2.imshow("Trajectory Execution", info_img)

            # Wait for key press
            while True:
                key = cv2.waitKey(0) & 0xFF

                if key == 32:  # SPACE key
                    print(f"\n>>> Executing movement to Step {current_step + 1}...")
                    try:
                        move_to_point(robot_param, point)
                        print(f"✓ Successfully moved to Step {current_step + 1}\n")
                        current_step += 1
                        break
                    except Exception as e:
                        print(f"✗ Error moving to Step {current_step + 1}: {e}")
                        import traceback
                        traceback.print_exc()
                        print(f"\nPress SPACE to retry, ESC to skip this point...")
                        continue

                elif key == 27:  # ESC key
                    print("\n>>> Skipping trajectory execution...")
                    current_step = len(trajectory)  # Exit the loop
                    break

        cv2.destroyWindow("Trajectory Execution")

        print("\n" + "="*80)
        print("TRAJECTORY EXECUTION COMPLETE")
        print("="*80 + "\n")
    else:
        print("Robot parameter not provided - skipping trajectory execution")

    plt.ioff()
    plt.close(fig)

# ------------ Main Program -----------

# painting_axis = PaintingAxis.Y
painting_axis = PaintingAxis.X
painting_direction = -1  # -1 = negative direction, +1 = positive direction

pivot = [-72.699, 602.14]

# Start a vision system in the background
start_vision_system()

# Main loop - display camera feed and wait for spacebar
print("\n=== Interactive Painting Transform ===")
print("Controls:")
print("  SPACE - Capture contours from camera")
print("  ESC   - Exit")
print("=====================================\n")

cv2.namedWindow("Camera Feed", cv2.WINDOW_NORMAL)

try:
    while True:
        # Display latest frame
        with frame_lock:
            if latest_frame is not None:
                display_frame = latest_frame.copy()

                # Add text overlay
                cv2.putText(display_frame, "Press SPACE to capture contours",
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, "Press ESC to exit",
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                cv2.imshow("Camera Feed", display_frame)

        # Handle keyboard input
        key = cv2.waitKey(30) & 0xFF

        if key == 27:  # ESC key
            print("Exiting...")
            break

        elif key == 32:  # SPACE key
            print("\n--- Capturing contours ---")

            # Request contour capture
            contour = get_contours_from_camera()
            print("Getting contour from camera...")
            print(f"Camera Contour: contour={contour}, type={type(contour)}")
            # pixel to mm
            TCP_X_OFFSET= -0.041
            TCP_Y_OFFSET =76.859
            transformed = applyTransformation(
                cameraToRobotMatrix=vision_system.cameraToRobotMatrix,
                contours=[contour],
                apply_transducer_offset=True,  # Enable transducer offset correction
                x_offset=TCP_X_OFFSET,
                # X offset in mm (configure based on your transducer)
                y_offset=TCP_Y_OFFSET,
                dynamic_offsets_config=None
                # Y offset in mm (configure based on your transducer)
            )
            print(f"Transformed contours: {transformed}, type={type(transformed)}")
            # applyTransformation returns a list of contours — extract the first one
            # Each contour is [[[x,y]], [[x,y]], ...] from numpy (n,1,2).tolist()
            contour = np.array(transformed[0], dtype=np.float32).reshape(-1, 1, 2)
            print(f"Extracted contour: {contour.shape}, {contour}")
            # contour = getRectangleShape((300,400), 200,100)
            # print(f"Synthetic contour (rectangle): contour={contour}, type={type(contour)}")
            if contour is not None and len(contour) > 0:
                # Ensure contour is a numpy array in the correct format
                if not isinstance(contour, np.ndarray):
                    contour = np.array(contour, dtype=np.float32).reshape(-1, 1, 2)
                elif contour.ndim == 2:
                    contour = contour.reshape(-1, 1, 2)

                # Get the captured frame
                with frame_lock:
                    captured_frame = latest_frame.copy() if latest_frame is not None else None

                # Calculate center of contour (do this once)
                M = cv2.moments(contour.astype(np.int32))
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    center = [cx, cy]
                else:
                    center = [int(np.mean(contour[:, 0, 0])),
                             int(np.mean(contour[:, 0, 1]))]

                # Draw the captured contour on the frame (no scaling needed)
                if captured_frame is not None:
                    display_captured = captured_frame.copy()
                    # Convert contour to int32 for drawing
                    contour_int = contour.astype(np.int32)
                    cv2.drawContours(display_captured, [contour_int], -1, (0, 255, 0), 2)

                    # Draw center (already calculated above)
                    cv2.circle(display_captured, tuple(center), 5, (0, 0, 255), -1)

                    # Show the captured frame with contour
                    cv2.imshow("Captured Contour", display_captured)
                    cv2.waitKey(0)
                    cv2.destroyWindow("Captured Contour")


                # Convert contour to a simple list of [x, y] points for the pipeline
                # From (n, 1, 2) to a list of [x, y]
                points = contour.reshape(-1, 2).tolist()

                # Ensure the contour is closed (first point == last point)
                if not np.array_equal(points[0], points[-1]):
                    points.append(points[0])

                print(f"Contour captured: {len(points)} points, center: {center}")
                print(f"Starting point: Point 0 at {points[0]}")
                print("Running transformation pipeline...")

                # Run the transformation pipeline with a robot parameter
                run_pipeline(points, center, pivot, "Painting Transform - Camera Contour",
                             robot_param=robot, axis=painting_axis, direction=painting_direction)

                # Return to camera feed
                cv2.destroyWindow("Painting Transform - Camera Contour")
                cv2.namedWindow("Camera Feed", cv2.WINDOW_NORMAL)

            else:
                print("Failed to capture contours. Try again.")

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nInterrupted by user")

finally:
    # Cleanup
    stop_vision_system()
    cv2.destroyAllWindows()
    print("Program ended.")

# ------------ Main Program END -----------
