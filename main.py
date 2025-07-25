"""Example usage of the HRVEstimator using MediaPipe Face Mesh."""

import cv2
import mediapipe as mp

from modules.hrv_rppg import HRVEstimator


def main() -> None:
    cap = cv2.VideoCapture(0)
    face_mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)
    estimator = HRVEstimator(fps=30)
    frame_count = 0
    bpm = None
    hrv = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
        landmarks = []
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            estimator.update(frame, landmarks)

        if frame_count % 30 == 0:
            data = estimator.compute()
            bpm = data["bpm"]
            hrv = data["hrv"]

        text = "BPM: N/D"
        if bpm is not None and hrv is not None:
            estado = "estresado" if hrv < 25 else "relajado"
            text = f"BPM: {bpm:.1f} | HRV: {hrv:.1f} ms ({estado})"
        elif bpm is not None:
            text = f"BPM: {bpm:.1f}"
        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("HRV", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        frame_count += 1

    face_mesh.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

