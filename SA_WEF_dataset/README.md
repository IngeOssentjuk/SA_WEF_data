# Water-Energy-Food Security Datasets for South Africa

## Description

This repository contains the code used to wrangle and merge various existing datasets into a newly created collection of 
datasets on household-level water-energy-food (WEF) security in South Africa. The security indicators are calculated at 
either household or municipal level, aggregated to the local municipality level, and have national coverage. The resulting
data is used for preparation of a scientific manuscript titled "A framework for spatially quantifying household-level 
Water-Energy-Food security: application to South Africa", currently under review in _Environmental and Sustainability 
Indicators_. Detailed descriptions of the calculations performed can be found in the metadata file accompanying the data 
collection (as published here: http://doi.org/10.15493/SARVA.42092023) and in the supplementary material to the manuscript.

## Installation

Clone this repository and install the dependencies from the pyproject.toml file. 

### Dependencies

Dependencies are listed in the pyproject.toml file

## Usage

This code can be used to reproduce the results of the manuscript mentioned under description, or to perform similar 
calculations using alternative thresholds/parameters, in order to assess sensitivity of the given results. Alternatively,
the code can be used to transfer the methodology described in the manuscript to other cases with similar raw data availability.

## Citation

Usage of the code does not require citation. If using the methodology for other cases or expanding on the current analysis,
please cite the accompanying manuscript and/or the datasets (if relevant). 

## How to contribute

If you are elaborating on the analysis performed using this repository, and want to contribute to the code, feel free to 
email me at [i.m.ossentjuk@uu.nl](mailto:i.m.ossentjuk@uu.nl).

## Funding

This repository was made for the project *Spatial inequality in water-energy-food security in South Africa; implications 
for public health and the consequences of climate change*, funded by NWO (grant number 482.22.105).

## Acknowledgments 

The author wants to thank Menno Straatsma for his help in setting up the raster calculations in Jupyter Notebook scripts, 
and Garrett Speed for his help in preparing publication of the repository. 