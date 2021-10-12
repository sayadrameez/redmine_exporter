# redmine_exporter
Redmine exporter for prometheus.io, written in python. Mainly inspired from github.com/lovoo/jenkins_exporter

## Usage

    redmine_exporter.py [-h] [-r redmine] [--user user]
                        [--password password] [-p port]

    optional arguments:
      -h, --help            show this help message and exit
      -r redmine, --redmine redmine
                            server url from the redmine api
      --user user           redmine api user
      --password password   redmine api password
      -p port, --port port  Listen to this port

#### Example

    docker run -d -p 9121:9121 sayadrameez/redmine_exporter:latest -r http://redmine:80 --user user --password password -p 9121


## Installation

    git clone git@github.com:sayadrameez/redmine_exporter.git
    cd redmine_exporter
    pip install -r requirements.txt

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request