# Information

This folder is mostly a work in progress. We need to cleanup the used/unused code and make it clear how users can add their own here.

* [TimeSeriesForecaster.py](./TimeSeriesForecaster.py) is a key file. It provides future-looking data and feeds it into the simulator window.  This is a very simple algorithm that uses a very basic time series. Users wishing for more complicated algorithms may want to modify this.

* We plan to clarify how forecasting works in terms of the simulator <https://github.com/microsoft/vasim/issues/20>.

* The [oracle](./models/oracle.py) forecaster in the `models` folder can be used feed 100% future-looking data to the algorithm, as it just feeds in the future data from the csv rather than making a prediction such as with TimeSeries.
