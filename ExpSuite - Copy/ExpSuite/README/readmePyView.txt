

Introduction to PyView with advice, tips&tricks, and examples of usage (last revised Mar 19, 2013). 
NOTE: In folder ExpSuite is stored the latest version of PyView (the one currently being used in Rm 563).

==============================================================================================================================
INSTALLATION (MAR 2013)
==============================================================================================================================

NOTE: The following is based on a successful re-installation of PyView and ancillary devices after HD failure in March 2013. 

0) Before getting started:
- Set power settings such that the computer NEVER goes to sleep (among other things, this prevents problems with the valves opening and remaining open when the computer is on sleep)
- Disable Windows automatic updates 
- Install DropBox and google Chrome

1) Python
The needed version of Python is 2.7 (2.7.2 was the release used by Alice, 2.7.3 was the release used after HD crach in March 2013).
Among the packages required for PyView are "bumpy", "scipy", "wxPython" (for GUI). Install Python with Python(x,y)­ as follows (info from Kyle Horn):
 
a. If python is already installed, uninstall python and all the packages 
b. download and run Python(x,y) from: http://ftp.ntua.gr/pub/devel/pythonxy/Python(x,y)­2.7.3.0.exe
with the recommended setup (which does not install all the packages; note that Python(x,y) only works on Windows). 

NOTE: Python(x,y) has all the packages required for PyView of the packages and the Spyder IDE, along with a wide selection of additional optional packages, and the installation is automatic. You'll know it's working if you can run Spyder (there will be a shortcut that will load it if one clicka the Start button and typea "Spyder" into the "Search programs and files" search box.). Downloads listed on the download page are for updates to an existing Python(x,y) installation. The above link is for a base install, which for some reason they hide inside the Mirror links on the download page. In general, most common python packages for Windows can be installed by downloading an automatic installer (usually an .exe or .msi file) rather than downloading the source and trying to install it yourself (which isn't hard, per se, but it does require knowing how to do it, and can be prone to failure.) If Python(x,y) didn't exist, I'd recommend looking for the .exe files for scipy and wxpython on their respective download pages, but you shouldn't have to bother, as Python(x,y) will do that for you.

2) PyView
Copy the ExpSuite folder from DropBox or any other backup device on the Desktop. At this state PyView will not work because of the unavailability of the NI card. 

3) NI card 
Install the drivers for the NI card with the DVD provided with the card. Restart the computer. Attach the NI card via USB port: it will recognize the device and quickly install the appropriate drivers automatically. At this point PyView should work. Try running it in 'device off' mode first. Then, hook the rest of the equipment and try a protocol that doesn't use tones, with the "device ON" option selected: it should work.

4) TNT Tone Generator
While the Tone Generator is unhooked from the computer, install the Software and Drivers for the tone generator from the DVD that came with the device. Shut off the computer and attach the Tone Generator to the PCI card inside the computer (if switching to a new computer, retrieve PCI card from old computer and insert it into new computer). The Tone Generator uses two cables to attach, the red one goes to the left, the blue one goes to the right (see photos). Restart the computer and switch the tone generator on. At this point, run the script 
"Tone Script 256 Tones.rcx"  
from folder "ToneScripts" in ExpSuite folder. On the top panel there is a box with a right arrow, press that: this will start the tone generator. You can use Python script "ToneControl.py" to stop (and/or restart) a tone. At this point, running PyView under "device ON" mode, with a paradigm that uses tones, should work.

NOTE: restarting the computer with the Tone Generator ON will most likely start a tone until you switch it off with ToneControl.py
NOTE: as of Mar 19th, trying to change the tone frequency in ToneControl.py raises an exception. Simply don't change tone frequency, this is only a means to start and stop a tone, and check that the device works.
5) The Stimulator
Install the drivers and the main software for the Stimulator from the Web following the instructions that came with the device. There is the possibility to install a 3rd software which provides tools to control the stimulator from external devices (like PyView, we guess): it is not necessary to install this 3rd software (see NOTE below).  
Once the software is installed, shut off the computer; attach stimulator via USB port, and restart the computer (I'm not 100% sure that a restart is required; also, the computer should recognize the device, but we got no notification of this happening. Still, it worked, keep reading). At this point run the software (not the drivers) that had been installed, from the icon that should now appear on the Desktop: this opens up a control panel to control and program the generator. Lucinda has in the past programmed the stimulator successfully, however as of March 2013 we have very limited experience with this. 

NOTE: The stimulator is not controlled by PyView. It used to, but this introduced temporal delays in sending TTL signals that was traced back to the attempt to run the Stimulator through PyView. However, the stimulator's own software will send a TTL signal to the Neuralynx amplifier, which will then be synchronized with the rest of the data, and the TTL address for the stimulator is known to the experimenter and thus available during data analysis. This setup is sufficient to run experiments with PyView that make use of the stimulator. As of March 2013, we have very limited experience with such type of experiment. 

6) This completes the installation of PyView and ancillary devices and the experimental suite should be ready to run. Other setup tips are:
- It is advisable to switch off all equipment including computers when not in use. 
- Perform backup manually once a day and then disconnect the backup drive from the computer.
- An anti-malware software recommended by Kyle was installed that is run only manually (typically, a quick scan); a fuller scan can be run if necessary, with the opportunity to remove malicious software. However, make sure not to erase drivers and other needed software that the anti-malware software may misidentify as malicious. 
- Internet should normally be disconnected and connected only when needed (for example, to backup log files into DropBox).
- If not done already, set power settings such that the computer NEVER goes to sleep, and disable Windows automatic updates (see pt. 0) above).


==============================================================================================================================
DESCRIPTION AND DOCUMENTATION
==============================================================================================================================

PyView allows to build paradigms using 'intervals' and 'actions'. Intervals can have associated actions to be executed at begin interval, at lever press, or at end interval. There are two types of actions: 'taste delivery and 'jump actions'. 
Jump actions allow to jump to intervals, with an option to jump to several intervals, each with a given probability. 
A special case of 'jump action' is 'start a new trial' (it is sufficient to check the associated box in the editor's interactive window for that action). A new trial is always marked by a TTL signal. If flow reaches the end of the last interval, a new trial is started and corresponding TTL (marking 'new trial') is sent to Amp.

--- NOTE: The examples of paradigms mentioned below are found in …/ExpSuite/TMP/EXAMPLES_OF_PARADIGMS.

*** WAIT interval *** the most basic interval. Doesn't do anything by default, but it can be linked to an action at beginning, at lever press, or at end of interval. After the action, the wait interval is continued until the end, unless the associated action instructs otherwise (and all subsequent lever presses, if associated to reward, are rewarded).

*** REWARD interval *** by default, this interval executes the associated action at lever press. The action can be changed 
from the default taste delivery, and can in turn trigger a second action (for example starting a new trial). If no second action is triggered, the flow continues until the end of the interval, as for example in the 'prova' version of the DMS task (Aug 27); subsequent lever presses however will be rewarded. The difference with a wait interval seems to be that in the latter an action (taste or jump) must be pre-defined and then linked to from the wait interval. A reward interval comes with its own default action, which is a taste action for historic reasons (which is also why it is called 'reward interval').

*** NOGO interval *** by default, this executes the associated action only if NO lever press occurred during the interval.
By default, the associated NOGO action is a delivery of taste, after which the flow proceeds to the next interval. 
Note that one can select what happens at lever press, that is, it is possible to leave the NOGO interval as soon as the lever is pressed, by associating a jump action to a lever press: i.e., if set to an action other than 'none', the lever press will trigger that action. NOTE how it is not possible to use a wait interval to mimic a NOGO interval (whereas it's possible to use a wait interval to mimic a REWARD interval). In a wait interval, a lever press could instruct not giving reward, but only by leaving the wait interval: waiting until the end of the wait interval and NOT delivering a reward, as required in a NOGO protocol, will not be possible (one could jump to a dummy interval after a lever press, but the total time spent from the beginning of the NOGO interval to the end of the dummy interval would be different each time). 

=== Examples and special cases:

1. In newGONOGO_24aug, one wants to have a tone just prior to any reward. To do this, one introduces a jump action to a tone followed by a dummy interval (=a wait interval during which nothing happens, no matter what), which at end of  interval  triggers a taste action. (Design: The dummy interval is to prevent the tone and the reward to occur simultaneously). Prior to the tone one introduces a dummy, short interval that triggers a new trial at end of interval: if a lever is pressed (NOGO condition violated), at the end of the NOGO interval one enters the dummy interval, after which a new trial starts. Note that the 'taste' action initially (and by default) associated with the NOGO interval should be deleted. 

2. The contrivance at pt. 1 is not present in the DMS task (27 Aug). So, at the end of a correct NOGO interval, reward is delivered and a post-reward action is triggered. This simply points to a dummy interval which, being the last interval of the paradigm, is followed by a new trial. NOTE that if the NOGO condition is violated, at the end of interval the NOGO action, and those 'children' actions triggered by the NOGO action, are *not* executed: the flow continues to the next interval (in this case, the postreward dummy interval).


==============================================================================================================================
USAGE AND TIPS
==============================================================================================================================

--- EDITOR: 

. Always add a manual rinse button to your paradigm that is not linked to anything, and never check box "create manual button" in a 'Taste' action -- see BUGS for rationale. 

. Use a different valve for 'Fake Click', i.e., a taste-delivery that opens a valve with no liquid. This will produce the 'click' sound but will not deliver anything. This is done to avoid a potential confound between response to click sound and response to actual reward, in case the neurons had acquired tuning to the click sound -- a secondary reward. Again, using a different valve gives a different TTL. 


--- PYVIEW: 

. BEFORE YOU RUN PYVIEW YOU MUST ACTIVATE THE TONE DEVICE: this is done through "Tone Script 256 Tones", to be started prior to PyView with "device ON" option is run. If errors occur, use 'ToneControl.py' to start or kill an ongoing tone (or to test the tone device).

. One can add random intervals to several durations to prevent anticipation directly from the PyView GUI (this is part of modifying the current protocol, not the paradigm: the paradigm is designed with the Editor, the protocol in an instance of the paradigm with a given choice of parameter values).


==============================================================================================================================
BUGS
==============================================================================================================================

. [log only: this doesn't affect the experimental paradigm]: if box "create manual button" is checked in a 'Taste' action, it is always logged as 'manual reward', whether it is a consequence of the events flow (e.g., self-delivered via lever-press, or coming at the end of a wait interval), or whether it was actually manually delivered via the 'Manual Reward' button.
Creating an independent "Manual Reward" button and un-checking the 'Create manual button" option in all other taste actions gets around this problem in addition to providing different TTL signals for manual- and paradigm-instructed taste deliveries.

. The first interval after a new trial is, in some situations, logged twice in the 'log' file; however, only one 'new trial' TTL is sent to the Amp, so this is only a  logging problem. 


==============================================================================================================================
FIXED BUGS
==============================================================================================================================

. Changing interval durations and/or adding variability to them from PyView control panel used to result in a number of bugs, including PyView crashes. These bugs were found after Alice had left (Sept 4, 2012). These were later corrected by Alice and it should be safe to change these parameters from PyView control panel (Nov 2012). 
 
