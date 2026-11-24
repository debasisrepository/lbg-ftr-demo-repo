"""Policy condition evaluators."""
from decimal import Decimal
from typing import Any, Callable, Dict


class ConditionEvaluator:
    """Registry and evaluator for policy conditions."""

    def __init__(self):
        self.evaluators: Dict[str, Callable] = {
            "field_present": self._eval_field_present,
            "decimal_greater_than": self._eval_decimal_greater_than,
            "field_in_set": self._eval_field_in_set,
            "field_equals_context": self._eval_field_equals_context,
            "collection_min_size": self._eval_collection_min_size,
            "sum_matches": self._eval_sum_matches,
            "all_belong_to": self._eval_all_belong_to,
            "one_of_present": self._eval_one_of_present,
            "flag_is_false": self._eval_flag_is_false,
        }

    def evaluate(self, condition_type: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a condition.
        
        Args:
            condition_type: Type of condition
            parameters: Condition parameters from rule
            context: Input context data
            
        Returns:
            True if condition passes, False otherwise
        """
        evaluator = self.evaluators.get(condition_type)
        if not evaluator:
            raise ValueError(f"Unknown condition type: {condition_type}")

        return evaluator(parameters, context)

    def _eval_field_present(self, params: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if field is present and not None."""
        field_path = params["field"]
        value = self._get_nested_field(context, field_path)
        return value is not None

    def _eval_decimal_greater_than(self, params: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if decimal field is greater than threshold."""
        field_path = params["field"]
        threshold = Decimal(str(params["threshold"]))
        value = self._get_nested_field(context, field_path)

        if value is None:
            return False

        return Decimal(str(value)) > threshold

    def _eval_field_in_set(self, params: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if field value is in allowed set."""
        field_path = params["field"]
        allowed_values = set(params["allowed_values"])
        value = self._get_nested_field(context, field_path)

        if value is None:
            return False

        return value in allowed_values

    def _eval_field_equals_context(self, params: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if two context fields are equal."""
        field1 = params["field"]
        field2 = params["context_field"]

        value1 = self._get_nested_field(context, field1)
        value2 = self._get_nested_field(context, field2)

        return value1 == value2

    def _eval_collection_min_size(self, params: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if collection has minimum size."""
        field_path = params["field"]
        min_size = params["min_size"]
        value = self._get_nested_field(context, field_path)

        if value is None:
            return False

        if not isinstance(value, (list, tuple)):
            return False

        return len(value) >= min_size

    def _eval_sum_matches(self, params: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if sum of collection field matches target."""
        collection_field = params["collection_field"]
        sum_field = params["sum_field"]
        target_field = params["target_field"]
        tolerance = Decimal(str(params.get("tolerance", "0.01")))

        collection = self._get_nested_field(context, collection_field)
        target = self._get_nested_field(context, target_field)

        if collection is None or target is None:
            return False

        total = sum(
            Decimal(str(self._get_nested_field(item, sum_field) or 0))
            for item in collection
        )
        target_decimal = Decimal(str(target))

        return abs(total - target_decimal) <= tolerance

    def _eval_all_belong_to(self, params: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if all items in collection belong to parent."""
        collection_field = params["collection_field"]
        item_parent_field = params["item_parent_field"]
        parent_id_field = params["parent_id_field"]

        collection = self._get_nested_field(context, collection_field)
        parent_id = self._get_nested_field(context, parent_id_field)

        if collection is None or parent_id is None:
            return False

        for item in collection:
            item_parent = self._get_nested_field(item, item_parent_field)
            if item_parent != parent_id:
                return False

        return True

    def _eval_one_of_present(self, params: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if at least one of the fields is present."""
        fields = params["fields"]

        for field_path in fields:
            value = self._get_nested_field(context, field_path)
            if value is not None:
                return True

        return False

    def _eval_flag_is_false(self, params: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if boolean flag is false."""
        field_path = params["field"]
        value = self._get_nested_field(context, field_path)

        if value is None:
            return True  # Treat None as false

        return value is False

    def _get_nested_field(self, obj: Any, field_path: str) -> Any:
        """Get nested field value using dot notation."""
        parts = field_path.split(".")
        current = obj

        for part in parts:
            if current is None:
                return None

            if isinstance(current, dict):
                current = current.get(part)
            else:
                current = getattr(current, part, None)

        return current


# Global evaluator instance
evaluator_registry = ConditionEvaluator()
