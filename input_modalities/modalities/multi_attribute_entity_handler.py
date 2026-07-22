class MultiAttributeEntityHandler:
    """
    Creates a multi-attribute entity input request.
    Example: medication, allergy, diagnosis.
    """

    def handle(
        self,
        question: str,
        entity: str,
        fields: list[tuple[str, str, str]]
    ):

        return {
            "type": "multi_attribute_entity",
            "question": question,
            "entity": entity,
            "fields": fields
        }
