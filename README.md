# VASIM

[![Build](https://github.com/microsoft/vasim/actions/workflows/pythonapp.yml/badge.svg)](https://github.com/microsoft/vasim/actions/workflows/pythonapp.yml)
[![coverage](https://codecov.io/gh/microsoft/vasim/branch/main/graph/badge.svg)](https://codecov.io/github/microsoft/vasim?branch=main)

VASIM (**V**ertical **A**utoscaling **SIM**ulator) is a tool designed to address the complexities involved in assessing autoscaling algorithms.

VASIM is designed for testing recommendation algorithms, with a particular focus on CPU usage in VMs and Kubernetes pods. The toolkit
replicates common components found in autoscaler architectures, including the controller, metrics collector, recommender, and
resource updater. It enables a comprehensive simulation of the entire autoscaling system’s behavior, with the flexibility to customize
various parameters.

If you are writing an academic paper, you can cite [this work](https://www.microsoft.com/en-us/research/publication/vasim-vertical-autoscaling-simulator-toolkit/) as:

```bibtex
@inproceedings{pavlenko2024vasim,
  author = {Pavlenko, Anna and Saur, Karla and Zhu, Yiwen and Kroth, Brian and Cahoon, Joyce and Camacho-Rodríguez, Jesús},
  title = {VASIM: Vertical Autoscaling Simulator Toolkit},
  booktitle = {IEEE International Conference on Data Engineering (ICDE 2024)},
  year = {2024},
  month = {May},
}
```

## Start here!

Our documentation and working example is in our [notebook](examples/using_vasim.ipynb) that shows how to get started simulating your data traces and tuning parameters.  Our example provides the 3 things needed to run VASim: (1) a data csv file, (2) an autoscaling algorithm, and (3) a metadata.json file of parameters. Details of all of these can be found in the notebook.

#### Additionally:

* Within each folder, there is a README explaining the code.
  * [simulator](simulator/README.md)
  * [recommender](recommender/README.md)
  * [forecasting](recommender/forecasting/README.md)
  * [cluster state](recommender/cluster_state_provider/README.md)
  * [tests](tests/README.md)

* For additional usage examples, see any test in the [tests](tests) folder that starts with `test_e2e`.

* Please see our [blog post](https://www.microsoft.com/en-us/research/blog/enhanced-autoscaling-with-vasim-vertical-autoscaling-simulator-toolkit/?msockid=0d2280e91b2c6ea41f32935e1a9f6f36) or [research paper](https://www.microsoft.com/en-us/research/publication/vasim-vertical-autoscaling-simulator-toolkit/) for more details!


## Authors

* Anna Pavlenko ([@apavlen](https://github.com/apavlen), primary implementation)
* Karla Saur ([@ksaur](https://github.com/ksaur), editing, maintaining)
* Yiwen Zhu ([@zyw400](https://github.com/zyw400))
* Brian Kroth ([@bpkroth](https://github.com/bpkroth))
* Joyce Cahoon ([@jyuu](https://github.com/jyuu))
* Jesús Camacho Rodríguez ([@jcamachor](https://github.com/jcamachor))


## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for techinical details.

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
