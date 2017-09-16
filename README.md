# arxivapp
Web Application (Django based) used for research in recommender systems on Arxiv (www.arxiv.org) system.

Our website: http://arxivapp.cs.mcgill.ca/.

# Implementation details
## Paths and dependencies
All current implementations are stored under `/home/ml/arxivapp`.
Python 2.7.6 is currently used. There are additional python packages (`python_social_auth` and its dependencies) installed in `/home/ml/arxivapp/python_packages`.

## Web server
The website is hosted with `apache2` installed with the OS. The apache configuration file is `/home/ml/arxivapp/apache2/arxiveapp.conf`. McGill administration should handle the routing between the apache2 host and the public [web site](http://arxivapp.cs.mcgill.ca/).
The current website is implemented using Django version `1.6`, which is very old compared to the current Django version. Perhaps an upgrade to the server will bring Django to newer version (e.g. `1.10` or `1.11`).

## Recommendation server
This server is basically a plain HTTP server that exclusively serves Django backend for recommendation purpose. Code for recommendation server resides under `/home/ml/arxivapp/site/arxivapp/learning_framework`.
To launch the server, simply run `cd /home/ml/arxivapp/site/arxivapp/learning_framework ; python manager.py`.

### LDA code
LDA code is stored under `/home/ml/arxivapp/site/arxivapp/lda`. Note that to allow LDA code to run, we need to manually install `gsl` library and add the installation path of this library into `LD_LIBRARY_PATH` at invocation time. This is already handled in file `/home/ml/arxivapp/site/arxivapp/lda/lda.py`. This file can be used as a reference of how to invoke lda code either manually or from python.

## Database
The backend database is MySQL version `5.5.46`. There is no special configuration to launch the MYSQL server. All settings are at default.

__There are two main performance indices created in the database.__ They are `last_name` for `main_app_author` table and `created_date` for `main_app_paper`. These indices significantly improve the load time of the site and therefore should be taken into consideration during development process.

## Jenkins
Jenkins are used to manage the daily tasks. The jenkins system can be found under `/home/ml/arxivapp/jenkins`. To launch Jenkins, it is recommended to reference the file `/home/ml/arxivapp/jenkins/launch_jenkins.py` to gather all the required runtime flags and the invocation process of Jenkins.
Currently there are two daily tasks in the system:
1. Update new papers from arxiv.org. It is __absolutely critical__ that this task finishes before midnight of the day, or the list of papers displayed on the page for that day will be incorrect. This task is named `Update projects`, which collects new papers from arxiv every night. Thanks to the created database indices, this task finishes very quickly. The code for this task can be found at `/home/ml/arxivapp/site/arxivapp/csv_extract.py`. Invocation details of this task can be found in the Jenkins task (go to `Configure` and look for `Execute Shell`).
In case this task fails to run for a period of time (e.g. Jenkins is brought down, server outage, ...), updates for the missing dates can be done manually using the sibling task `Update_with_dates`. It is worth noting that the date for the update used is actually the next calendar date (e.g. if we want to do update for thursday night we have to call it with friday calendar date).
2. Retrain the gmf model with the updated papers by calling the recommendation server to execute the retrain function. This task is named `Retrain model`. It is important that this is run __after__ the update task above finishes. This task is usually very time consuming, and its runtime is increasing every day as the amount of paper increases. However, the underlying code performs an atomic replacement of the existing model, which means that the recommendation server can still serve the old model while the new model is being trained.

## Tmux
We are currently using `tmux` to maintain the Jenkins server and recommendation server processes so that they do not terminate at the end of the ssh session. In the future, any other equivalent method is also acceptable.
