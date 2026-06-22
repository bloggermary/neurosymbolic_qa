from modalities.boolean_handler import BooleanHandler
from modalities.numeric_handler import NumericHandler
from modalities.string_handler import StringHandler


class ModalityRouter:
    """
    Routes modality-specific questions to the correct handler.
    """

    def __init__(self):
        self.boolean_handler = BooleanHandler()
        self.numeric_handler = NumericHandler()
        self.string_handler = StringHandler()
        self.scale_handler = ScaleHandler()
        self.frequency_handler = FrequencyHandler()
        self.medication_handler = MedicationHandler()
        self.medical_history_handler = MedicalHistoryHandler()
        self.family_history_handler = FamilyHistoryHandler()

    def route_boolean(self, question: str) -> bool:
        return self.boolean_handler.handle(question)

    def route_numeric(self, question: str) -> float:
        return self.numeric_handler.handle(question)

    def route_string(self, question: str) -> str:
        return self.string_handler.handle(question)

    def route_scale(self, question: str, scale_min: int, scale_max: int) -> int:
        return self.scale_handler.handle(question, scale_min, scale_max)

    def route_frequency(self, question: str, options: list[str]) -> str:
        return self.frequency_handler.handle(question, options)

    def route_medication(self, question: str, options: list[str]) -> str:
        return self.medication_handler.handle(question, options)

    def route_medical_history(self, question: str) -> str:
        return self.medical_history_handler.handle(question)

    def route_family_history(self, question: str) -> str:
        return self.family_history_handler.handle(question)

router = ModalityRouter()


def route_boolean(question: str) -> bool:
    return router.route_boolean(question)


def route_numeric(question: str) -> float:
    return router.route_numeric(question)


def route_string(question: str) -> str:
    return router.route_string(question)


def route_scale(question: str, scale_min: int, scale_max: int) -> int:
    return router.route_scale(question, scale_min, scale_max)


def route_frequency(question: str, options: list[str]) -> str:
    return router.route_frequency(question, options)


def route_medication(question: str, options: list[str]) -> str:
    return router.route_medication(question, options)


def route_medical_history(question: str) -> str:
    return router.route_medical_history(question)


def route_family_history(question: str) -> str:
    return router.route_family_history(question)