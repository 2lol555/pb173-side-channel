# General information
This repository contains files pertaining to the course **PB173 Tematicky zameraný vývoj aplikácií** with the subsection of **Side channel analysis**. The project theme is trace alignment, and it contains/will contain multiple approaches to aligning trace files.

You can run a quick demo by running `demo.sh` using the command line.

# Third party requirements
## pip packages
- trsfile
- numpy
- matplotlib
- tqdm
- docopt

# Currently implemented alignment methods
## Peak alignment
### About
In peak alignment, the code searches for a peak in a specified window within the traces and then shifts the traces to align said peak.
### Outputs
The project currently aligns the traces, saves the aligned traces as a new file and runs a correlation script on them, showing you, whether the correlation could extract any data.
### Usage
1. Install all prerequisites listed in the readme using the command `pip install -r requirements.txt`
2. Clone the repository
3. Run the command `python3 alignment.py "path to .trs file"`
### Example of usage
- Trs file can be found ["here"](https://is.muni.cz/auth/de/536539/AES_fixed_rand_input_CAFEBABEDEADBEEF0001020304050607_SAVEEVEN_0_1000_MIS_1000_.trs)
- Peak alginment
    `python3 alignment.py -s 14000 -w 4000 -n 1000 AES_fixed_rand_input_CAFEBABEDEADBEEF0001020304050607_SAVEEVEN_0_1000_MIS_1000_.trs`
- Correlation alignment
    `python3 alignment.py -c True -w 4000 -n 1000 AES_fixed_rand_input_CAFEBABEDEADBEEF0001020304050607_SAVEEVEN_0_1000_MIS_1000_.trs`
### Planned improvements
Implement analyzing the peak according to the window resample values in the traces.
