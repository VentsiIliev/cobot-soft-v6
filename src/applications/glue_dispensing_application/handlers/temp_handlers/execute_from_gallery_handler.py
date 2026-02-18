import matplotlib
import numpy as np


matplotlib.use('Agg')  # Use non-interactive backend

from applications.glue_dispensing_application.settings.enums import GlueSettingKey
from modules.utils import utils
from modules.utils.path_interpolation import combined_interpolation, debug_plotting


def execute_from_gallery(application,workpiece,z_offset_for_calibration_pattern):
    def flatten_point(p):
        """Flattens nested point lists like [[[x, y]]] -> [x, y]"""
        while isinstance(p, (list, tuple)) and len(p) == 1:
            p = p[0]
        return p

    # print("Handling execute from gallery: ", workpiece)
    robotPaths = []
    points_only = []

    # Process both Contour and Fill patterns if available
    for pattern_type in ["Contour", "Fill"]:
        sprayPatternsList = workpiece.sprayPattern.get(pattern_type, [])
        if not sprayPatternsList:
            print(f"No {pattern_type} patterns found, skipping...")
            continue

        print(f"Processing {pattern_type} patterns: {len(sprayPatternsList)} patterns found")

        for pattern in sprayPatternsList:
            contour_arr = pattern.get("contour", [])
            fill_arr = pattern.get("fill", [])
            contour_arr_settings = pattern.get("settings", {})
            print(f"[EXECUTE_FROM_GALLERY] contour_arr_settings {contour_arr_settings}")
            # Sanitize and convert points to float
            points = []

            for p in contour_arr:
                coords = p[0] if isinstance(p[0], (list, tuple, np.ndarray)) else p
                # Ensure coords[0] and coords[1] are scalars
                x = float(coords[0])
                y = float(coords[1])

                points.append([x, y])

            if points:
                print(f"=== HANDLEEXECUTEFROMGALLERY {pattern_type} TRANSFORMATION DEBUG ===")
                print(f"Input points type: {type(points)}")
                print(f"Input points sample: {points[:3] if len(points) > 3 else points}")

                # Prepare points for OpenCV: shape (N, 1, 2)
                np_points = np.array(points, dtype=np.float32).reshape(-1, 1, 2)
                print(f"After np.array reshape: shape={np_points.shape}, dtype={np_points.dtype}")
                print(f"np_points sample: {np_points[:3] if len(np_points) > 3 else np_points}")

                # Transform to robot coordinates
                # print(f"Camera to robot matrix: {self.visionService.cameraToRobotMatrix}")
                transformed = utils.applyTransformation(application.visionService.cameraToRobotMatrix, np_points,
                                                        x_offset=application.get_transducer_offsets()[0],
                                                        y_offset=application.get_transducer_offsets()[1],
                                                        dynamic_offsets_config=application.get_dynamic_offsets_config())
                # print(f"After transformation: type={type(transformed)}, shape={transformed.shape if hasattr(transformed, 'shape') else 'no shape'}")
                # print(f"Transformed sample: {transformed[:3] if len(transformed) > 3 else transformed}")

                finalContour = []
                for i, point in enumerate(transformed):
                    # print(f"Processing point {i}: {point}")
                    point = flatten_point(point)
                    # print(f"After flatten_point: {point}")
                    x = float(point[0])
                    y = float(point[1])
                    # print(f"Final x,y: {x}, {y}")

                    z_str = str(contour_arr_settings.get(GlueSettingKey.SPRAYING_HEIGHT.value)).replace(",",
                                                                                                             "")
                    z = float(z_str)
                    z = application.robotService.robot_config.safety_limits.z_min + z
                    print(f"z_min + z = {application.robotService.robot_config.safety_limits.z_min} + {z} = {z}")
                    rx = 180
                    ry = 0
                    rz = float(contour_arr_settings.get(GlueSettingKey.RZ_ANGLE.value, 0))

                    newPoint = [x, y, z, rx, ry, rz]
                    finalContour.append(newPoint)

                robotPaths.append([finalContour, contour_arr_settings])
                points_only.append(finalContour)
                print(f"Added {pattern_type} path with {len(finalContour)} points")

    # application.robotService.move_to_calibration_position(z_offset=z_offset_for_calibration_pattern)
    # self.robotService.cleanNozzle()
    # print(f"Moving to calibration position with z_offset={z_offset_for_calibration_pattern}")
    # move_result = application.robotService.move_to_calibration_position(z_offset=z_offset_for_calibration_pattern)
    # if move_result != 0:
    #     print(f"Failed to move to calibration position, result={move_result}")
    #     return
    # print("Successfully moved to calibration position")

    # Two-stage interpolation with ADAPTIVE density based on segment length
    # Use adaptive spacing and spline density multiplier from segment settings
    # Long segments get more points, short segments get fewer points
    linear_interpolated = []
    spline_interpolated = []

    for i, path in enumerate(points_only):
        # Get settings for this path
        settings = robotPaths[i][1] if i < len(robotPaths) else {}
        adaptive_spacing = float(settings.get(GlueSettingKey.ADAPTIVE_SPACING_MM.value, "10.0"))
        spline_multiplier = float(settings.get(GlueSettingKey.SPLINE_DENSITY_MULTIPLIER.value, "2.0"))
        smoothing_lambda = float(settings.get(GlueSettingKey.SMOOTHING_LAMBDA.value, "0.0"))

        print(f"Path {i+1}: Adaptive spacing = {adaptive_spacing}mm, Spline density = {spline_multiplier}x, Smoothing λ = {smoothing_lambda}")
        linear, spline = combined_interpolation.interpolate_path_two_stage(
            path,
            adaptive_spacing_mm=adaptive_spacing,
            spline_density_multiplier=spline_multiplier,
            smoothing_lambda=smoothing_lambda
        )
        linear_interpolated.extend(linear)  # Combine all paths into one
        spline_interpolated.extend(spline)  # Combine all paths into one

    print(f"Combined interpolation: {len(points_only)} path(s) → {len(linear_interpolated)} linear pts → {len(spline_interpolated)} spline pts")

    # write the spline interpolated points to a txt file
    with open('interpolated_points.txt', 'w') as f:
        for point in spline_interpolated:
            f.write("%s\n" % point)

    # Plot the points for debug with different colors for linear and spline
    # Wrap combined paths in lists for plotting compatibility
    if points_only and linear_interpolated and spline_interpolated:
        combined_original = []
        for path in points_only:
            combined_original.extend(path)
        debug_plotting.plot_trajectory_debug([combined_original], [linear_interpolated], [spline_interpolated])
    #
    # Execute trajectory with a combined spline interpolated path
    velocity = application.robotService.robot_config.global_motion_settings.global_velocity
    acceleration = application.robotService.robot_config.global_motion_settings.global_acceleration

    """EXECUTE VIA ROS2"""
    # print(f"Executing combined trajectory with {len(spline_interpolated)} total points, vel={velocity}, acc={acceleration}")
    # result = application.robotService.robot.execute_trajectory(spline_interpolated, vel=velocity, acc=acceleration, blocking=True)
    #
    # if result == 0:
    #     print("✓ Trajectory execution completed successfully")
    # else:
    #     print(f"✗ Trajectory execution failed with result={result}")

    """EXECUTE VIA FAIRINO SDK"""
    # try:
    #     application.glue_dispensing_operation.start(robotPaths, spray_on=application.get_glue_settings().get_spray_on())
    # except Exception as e:
    #     import traceback
    #     traceback.print_exc()
    #     print(f"⚠️ Error during glue dispensing operation: {e}")
    # print("Paths to trace: ", robotPaths)

    """EXECUTE VIA TEST ROBOT FOR DEBUGGING"""
    result = application.robotService.robot.execute_trajectory(robotPaths, vel=velocity, acc=acceleration, blocking=True)