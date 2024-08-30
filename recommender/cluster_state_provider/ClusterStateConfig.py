import json


class ClusterStateConfig(dict):
    def __init__(self, config_dict=None, filename=None):
        super().__init__()  # Initialize the dictionary part of the object
        if config_dict is not None:
            self.update(config_dict)
        elif filename is not None:
            self.load_from_json(filename)

    def load_from_json(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
            self.update(data)  # Use update method to merge loaded data
            for key, value in data.items():  # Update attributes
                setattr(self, key, value)

    def to_json(self, filepath):
        try:
            with open(filepath, 'w') as f:
                json.dump(self, f, indent=4)
            print("JSON file successfully written.")
        except Exception as e:
            print(f"Error writing JSON file: {e}")

    def __setattr__(self, name, value):
        self[name] = value
        super().__setattr__(name, value)
