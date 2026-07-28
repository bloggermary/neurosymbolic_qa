class MultiAttributeEntityHandler:
    """
    Creates a multi-attribute entity input request.
    Example: medication, allergy, diagnosis.
    """

    def handle(
        self,
        question: str,
        entity: str,
        fields: list[list[str]]
    ) -> dict:

        return {
            "type": "multi_attribute_entity",
            "question": question,
            "entity": entity,
            "fields": fields
        }
