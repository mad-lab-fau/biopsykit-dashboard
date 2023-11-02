# General Info

## What is Biopsykit - Dashboard?

The Biopsykit - Dashboard is a web application that provides a graphical user interface (GUI) for the Python 
package [biopsykit](https://github.com/mad-lab-fau/biopsykit). It utilizes the Python package 
[panel](https://panel.holoviz.org/) to create the GUI and [pyodide](https://pyodide.org/en/stable/) in order to build 
it as a [WASM](https://webassembly.org) progressive web application. This allows the Biopsykit - Dashboard to be
hosted on [Github Pages](https://pages.github.com) and be used in the browser without the need to install any software.
This makes it easier to use the Biopsykit - Dashboard for users that are not familiar with Python or the command line.

## How to use the Biopsykit - Dashboard?

<img src="dashboard_main_menu.png" alt="Main Menu" border-effect="line"/>

The Biopsykit - Dashboard can be accessed via the following link: 
[Dashboard](https://mad-lab-fau.github.io/biopsykit-dashboard/). After the installation you can select the types of 
data which you want to analyze. At the moment there are implementation for the following signal types:

<ul>
    <li> Physiological Signals </li>
    <li> Questionnaire Data </li>
    <li> Saliva Data</li>
    <li> Sleep Data </li>
</ul>

The data type Psychological Data is currently under development and at this point not available. After selecting the
data type you will be guided through the analysis process. For each data type there are different analysis options, 
and you can observe your progress at the top of the page. After finishing the analysis you can download the results 
in the last step as a zip file.

### Usage as a Progressive Web App

In the Chrome Browser you can also Download the Biopsykit - Dashboard as a Progressive Web App (PWA). This allows you 
to use the Biopsykit - Dashboard as a standalone application on your computer. To do so, click on the icon in the 
address bar of your browser which is highlighted under the red circle in the following image:

<img src="Chrome_install_as_pwa.png" alt="PWA Icon" border-effect="line"/>

After clicking on the icon you will be asked if you want to install the Biopsykit - Dashboard as a PWA. After that you 
can confirm the installation of the Panel Applications and the Biopsykit - Dashboard will be installed on your computer.

<img src="Confirm_pwa_installation.png" alt="Confirm installation" border-effect="line"/>

## How to report issues or request new features?

If you encounter any issues or have ideas for new features, please report them to the 
[GitHub repository](https://github.com/mad-lab-fau/biopsykit-dashboard) under the issues tab.
