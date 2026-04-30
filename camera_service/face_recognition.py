class FaceRecognitionAdapter:
    """Boundary for OpenCV face recognition.

    Move the tested recognition code from EDUCAM123 here later. The web app should
    never depend directly on cv2 windows, camera streams, or local face folders.
    """

    def __init__(self, faces_dir):
        self.faces_dir = faces_dir

    def recognize(self, frame):
        raise NotImplementedError("Connect the existing OpenCV recognition code here.")

