def find_data_objects_with_context(structure, target_type, key=None, results=None):
    """
    Recursively searches through nested structures and returns a list of tuples.
    Each tuple contains (found_object, parent_container, key_or_index).

    Args:
        structure: The current dict, list, or object being searched.
        target_type: The type of object to find.
        results: A list to store the found object and its context.

    Returns:
        A list of (object, parent_container, key_or_index) tuples.
    """
    if results is None:
        results = []

    # 1. If it's a Dictionary, iterate through its items
    if isinstance(structure, dict):
        for key, value in structure.items():
            # # Check if the value is the target object
            # if isinstance(value, target_type):
            #     # Save the object and its context (parent and key)
            #     results.append((value, structure, key))

            # Continue recursion on the value
            find_data_objects_with_context(value, target_type, key, results)

    # 2. If it's a List, iterate through its elements using indices
    elif isinstance(structure, list):
        for i in range(len(structure)):
            element = structure[i]

            # Check if the element is the target object
            if isinstance(element, target_type):
                # Save the object and its context (parent and index)
                results.append((element, structure, key, i))

            # Continue recursion on the element
            find_data_objects_with_context(element, target_type, key, results)

    # Return the collected results
    return results


# --- Example Usage ---


class Data:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"<Data Object: {self.name}>"


TARGET_CLASS = Data

# The nested data structure
data_structure = {
    # Key: 'parent_key'
    "parent_key": {
        # Key: 'outer_sub_item'
        "outer_sub_item": [
            {
                # Key: 'inner_dict'
                "inner_dict": {
                    # Key: 'inner_sub_item' (DIREKT ÜBER DATA-OBJEKT)
                    "inner_sub_item": Data("Beta")
                }
            }
        ]
    },
    "main_data": Data("Alpha"),
}

# 1. Execute the search to get objects AND their context
# The result is a list of tuples: [(object, parent, key/index), ...]
context_list = find_data_objects_with_context(data_structure, TARGET_CLASS)

# 2. Now you can iterate over the list and replace objects in the original structure
print("--- Replacing Objects in the Original Structure ---")

# Access the second found object's context (Data('Beta'))
# context_list[1] is the tuple: (Data('Beta'), data_structure['batch_1'], 2)
object_to_replace, parent_container, key_or_index = context_list[1]

print(f"Replacing Object: {object_to_replace.name} at key/index: {key_or_index}")

# The actual replacement in the data_structure:
parent_container[key_or_index] = {}  # Write an empty dict to the original spot

# 3. Check the result
print("\n--- Final Data Structure (after replacement) ---")
import json

# Using default=str to handle any remaining Data objects nicely
print(json.dumps(data_structure, indent=2, default=str))
