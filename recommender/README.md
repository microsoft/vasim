# Recommenders

This is the directory with some sample recommenders. To implement a recommender you will need to create a file for your algorithm, add any paramters you need to the `__init__` function and then implement the core logic of your recommender in the `run()` function.

```python
class SimpleAdditiveRecommender(Recommender):
    def __init__(self, cluster_state_provider, save_metadata=True):
        # Copy the code at the top of this function as-is.

        # Put your parameters here hard-coded, or pass them in to your
        # `metadata.json` file in the `algo_specific_config` section.
        self.my_param = self.algo_params.get("myparam", 2)

    def run(self, recorded_data):
        """
        This method runs the recommender algorithm and returns the new number of
              cores to scale to (new limit).

        Inputs:
            recorded_data (pd.DataFrame): The recorded metrics data for the current time window to simulate
        Returns:
            latest_time (datetime): The latest time of the performance data.
            new_limit (float): The new number of cores to scale to.
        """

        # Your logic goes here! Look at the data in the `recorded_data` dataframe,
        #   do a calculation, and return the number of cores to scale to.

        return new_limit
```
