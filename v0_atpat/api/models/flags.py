'''class Flags:
    def __init__(self, test_id, student_id, flag_type, timestamp, details, to_review):
        self.test_id = test_id
        self.student_id = student_id
        self.flag_type = flag_type
        self.timestamp = timestamp
        self.details = details
        self.to_review = to_review
'''
class Flags:
    def __init__(
        self,
        test_id,
        mis_id,
        parenturl,
        start_time,
        end_time,
        no_face,
        multi_face,
        off_gaze,
        alt_tab,
        audio_events,
        typing_events,
        avg_wpm,
        backspace_ratio,
        typing_flags,
        proofs,
        to_review=False
    ):
        self.test_id = test_id              # Which test this belongs to
        self.mis_id = mis_id                # Student’s MIS ID
        self.parenturl = parenturl          # Parent test URL (e.g., leetcode.com)
        self.start_time = start_time
        self.end_time = end_time
        self.no_face = no_face
        self.multi_face = multi_face
        self.off_gaze = off_gaze
        self.alt_tab = alt_tab
        self.audio_events = audio_events
        self.typing_events = typing_events
        self.avg_wpm = avg_wpm
        self.backspace_ratio = backspace_ratio
        self.typing_flags = typing_flags
        self.proofs = proofs                # list of dicts: [{type, path, ts}, ...]
        self.to_review = to_review          # Student/admin can toggle this
