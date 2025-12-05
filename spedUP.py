import cv2

def speed_up_video(input_path, output_path, speed_factor=2.0):
    """
    Speeds up a video by the given factor.
    Example: speed_factor=2.0 → 2x faster (half duration)
    """

    # Read input video
    cap = cv2.VideoCapture(input_path)

    if not cap.isOpened():
        raise Exception("Could not open input video file.")

    # Get input video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Output video writer (same resolution, increased FPS)
    out = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps * speed_factor,    # Increase FPS to speed up
        (width, height)
    )

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)

    cap.release()
    out.release()
    print(f"Saved sped-up video to: {output_path}")


# Example usage
if __name__ == "__main__":
    speed_up_video(
        input_path="/workspaces/athena_AI_assignment/data/videos/one_more_test.mp4",
        output_path="/workspaces/athena_AI_assignment/results/output_fastest.mp4",
        speed_factor=2.0   # 2x faster
    )
