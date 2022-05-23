## About
Terminal Live is an AI programming competition featuring over 30,000 of the world’s best engineers and data scientists. The Spring 2022 Terminal Live season included virtual events for hundreds of students at the most prestigious universities in the US, Canada, Europe and Asia. At each competition, teams coded algorithms for a tower defense-style strategy game, and competed head-to-head in a single-elimination tournament.

Our team, Murphy's Lawyers, consisted of myself, [Stan](https://github.com/stan-hua), and [George](https://github.com/CardboardTank), three UofT computer science students whom met each other due to a shared interest in AI and algorithms. Together, we developed the FUNNEL algorithm using python, which placed #5 out of 24 teams against top competitors from CMU, UMich, and UIUC.

The starter kit provided by Correlation One can found [here](https://github.com/correlation-one/C1GamesStarterKit).

Here is preview of our algorithm in action:
<video src="https://user-images.githubusercontent.com/72905894/169751007-d641819e-8439-4b55-aacb-aba2352ecb38.mov">

To learn more about the game and competition itself, check out the [main site](https://terminal.c1games.com/rules).


## Competition Results
Team: Murphy's Lawyers

Placed #5 in 24 teams.
Certificate of participation: https://www.credential.net/64c4b845-a462-4c77-8262-e4ca827b1abf

Top 10 Placements:
https://terminal.c1games.com/competitions/293/profile/19626
<img width="1034" alt="image" src="https://user-images.githubusercontent.com/72905894/162841899-7016fec6-8bc0-4f10-8ddd-a01a2eaf4d12.png">

## Usage

To test the algo locally, you should use the test_algo_[OS] scripts in the scripts folder. Details on its use is documented in the README.md file in the scripts folder.

For programming documentation of language specific algos, see each language specific README.
For documentation of the game-config or the json format the engine uses to communicate the current game state, see json-docs.html

## Windows Setup

If you are running Windows, you will need Windows PowerShell installed. This comes pre-installed on Windows 10.
Some windows users might need to run the following PowerShell commands in adminstrator mode (right-click the 
PowerShell icon, and click "run as administrator"):
    
    `Set-ExecutionPolicy Unrestricted`
    
If this doesn't work try this:
    
    `Set-ExecutionPolicy Unrestricted CurrentUser`
    
If that still doesn't work, try these below:
    
    `Set-ExecutionPolicy Bypass`
    `Set-ExecutionPolicy RemoteSigned`
    
And don't forget to run the PowerShell as admin.

## Troubleshooting

For detailed troubleshooting help related to both website problems and local development check out [the troubleshooting section](https://terminal.c1games.com/rules#Troubleshooting).

#### Python Requirements

Python algos require Python 3 to run. If you are running Unix (Mac OS or Linux), the command `python3` must run on 
Bash or Terminal. If you are running Windows, the command `py -3` must run on PowerShell.
   
#### Java Requirements

Java algos require the Java Development Kit. Java algos also require [Gradle]
(https://gradle.org/install/) for compilation.
   
## Running Algos

To run your algo locally or on our servers, or to enroll your algo in a competition, please see the [documentation 
for the Terminal command line interface in the scripts directory](https://github.com/correlation-one/AIGamesStarterKit/tree/master/scripts)
