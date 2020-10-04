# squiRL
An RL library in PyTorch embedded within the PyTorch Lightning framework.

## Branch names
Branches should be using one of these groups to start with:
wip - Works in progress; stuff I know won't be finished soon (like a release)
feat - Feature I'm adding or expanding
bug - Bug fix or experiment
junk - Throwaway branch created to experiment

Groups should be split using "-". For example: junk-id-test

Skip the ID for now, since we don't have unique id generation in trello. Please add a label with the branch name to the card.

## Commit messages
Commit your work as often as possible. Push the changes in batches.
Each commit should have one line for each feature/change added.

Example of commit:
File x.py added 
Gradient clipping fixed  
Feature Y implemented  

## Pull Requests
When finished with your work, create a pull request between the relevant branches. This would be discussed in our next meeting. Please add a label to trello to mark cards in need of review.

## Unit Testing
Any script you add in the tests directory with the name test_….py like the script already there: `test_MLP_output_shape.py` will run automatically when you merge to master. Or when you create a pull requests.  
So just come up with a test, add it to the tests folder and voila.  
When you are developing on the command line and you want to run the tests locally, go to the tests directory and run `pytest` on the command line. This will run all the tests in the directory.  
You would need to install the `pytest` module from pip first of course.
