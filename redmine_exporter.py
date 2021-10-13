#!/usr/bin/python

import re
import time
import requests
import argparse
from pprint import pprint
import json

import os
from sys import exit
from prometheus_client import start_http_server, Summary
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from redminelib import Redmine
import jsonpickle
import pydash
import ciso8601
# redmine_project_open_issues_total_count
# redmine_project_closed_issues_total_count
# redmine_project_issue_estimated_duration_hours
# redmine_project_issue_done_ratio
# redmine_project_issue_spenttime_duration_hours


DEBUG = int(os.environ.get('DEBUG', '0'))

COLLECTION_TIME = Summary('redmine_collector_collect_seconds', 'Time spent to collect metrics from Redmine')

class RedmineCollector(object):
    # The build apimetrics we want to export about.
    apimetrics = ["redmine_project_open_issues_total_count", "redmine_project_closed_issues_total_count",
                "redmine_project_issue_estimated_duration_hours", "redmine_project_issue_done_ratio", "redmine_project_issue_changesets_total_count"
                "redmine_project_spenttime_duration_hours","redmine_project_issue_due_date","redmine_project_issue_start_date","redmine_project_issue_closed_date"
                ]

    def __init__(self, target, user, password):
        self._target = target.rstrip("/")
        self._user = user
        self._password = password

    def collect(self):
        start = time.time()
        self._setup_empty_prometheus_metrics()
        # Request data from Redmine
        jobs = self._request_data()        

        for status in self.apimetrics:
            for metric in self._prometheus_metrics.values():
                yield metric

        duration = time.time() - start
        COLLECTION_TIME.observe(duration)

    def _request_data(self):
        # Request exactly the information we need from Redmine
        redmine = Redmine(self._target, username=self._user,password= self._password)
       
        for project in redmine.project.all():
            count = len(redmine.issue.filter(status_id='open',project_id=project.id))
            self._prometheus_metrics['openissues'].add_metric([project.name], count)
            count = len(redmine.issue.filter(status_id='closed',project_id=project.id))
            self._prometheus_metrics['closedissues'].add_metric([project.name], count)    

        for issue in redmine.issue.all(include=['relations', 'time_entries','changesets']):
            # js = jsonpickle.encode(issue)
            # print(js)
            # status=pydash.get(issue,"_decoded_attrs.status.name")
            status=pydash.get(issue,"_decoded_attrs.status.name")
            tracker=pydash.get(issue,"_decoded_attrs.tracker.name")
            priority=pydash.get(issue,"_decoded_attrs.priority.name")            
            issueid =str(issue.id)
            estimatedhours = getattr(issue, 'estimated_hours',None)
            doneratio= getattr(issue, 'done_ratio',None)        
            duedate = getattr(issue, 'due_date',None)
            startdate= getattr(issue, 'start_date',None)
            closeddate= getattr(issue, 'closed_on',None)           

            if estimatedhours:
                self._prometheus_metrics['estimatedduration'].add_metric([project.name,issueid,status,tracker,priority], estimatedhours)
            if doneratio:            
                self._prometheus_metrics['doneratio'].add_metric([project.name,issueid,status,tracker,priority], int(doneratio/100))
            if issue.time_entries:
                for timetracker in issue.time_entries:                    
                    self._prometheus_metrics['spentime'].add_metric([project.name,issueid,timetracker.activity.name],str(timetracker.hours))
            changesetscount = 0
            if issue.changesets:
                changesetscount = len(issue.changesets)
            self._prometheus_metrics['changesets'].add_metric([project.name,issueid,status,tracker,priority],changesetscount)
            if duedate:
                # ts = ciso8601.parse_datetime(duedate)
                # to get time in seconds:
                duetimestamp = time.mktime(duedate.timetuple())
                self._prometheus_metrics['duedate'].add_metric([project.name,issueid,status,tracker,priority],duetimestamp)
            if startdate:
                # ts = ciso8601.parse_datetime(startdate)
                # to get time in seconds:
                starttimestamp = time.mktime(startdate.timetuple())
                self._prometheus_metrics['startdate'].add_metric([project.name,issueid,status,tracker,priority],starttimestamp)
            if closeddate:
                # ts = ciso8601.parse_datetime(startdate)
                closetimestamp = time.mktime(closeddate.timetuple())
                self._prometheus_metrics['closeddate'].add_metric([project.name,issueid,status,tracker,priority],closetimestamp)


    def _setup_empty_prometheus_metrics(self):
        # The metrics we want to export.
        self._prometheus_metrics = {}
        
        # snake_case = re.sub('([A-Z])', '_\\1', status).lower()
        
        self._prometheus_metrics['openissues'] = GaugeMetricFamily('redmine_project_open_issues_total_count',
                                    'Redmine Project Open Issues Count', labels=["projectname"])
        self._prometheus_metrics['closedissues'] = GaugeMetricFamily('redmine_project_closed_issues_total_count',
                                    'Redmine Project Closed Issues Count', labels=["projectname"])
        self._prometheus_metrics['estimatedduration'] = GaugeMetricFamily('redmine_project_issue_estimated_duration_hours',
                                    'Redmine Project Issue Estimated Duration in Hours', labels=["projectname","issueid","status","tracker","priority"])
        self._prometheus_metrics['doneratio'] = GaugeMetricFamily('redmine_project_issue_done_ratio',
                                    'Redmine Project Issue Done Ratio', labels=["projectname","issueid","status","tracker","priority"])
        self._prometheus_metrics['changesets'] = GaugeMetricFamily('redmine_project_issue_changesets_total_count',
                                    'Redmine Project Issue ChangeSets Total Count', labels=["projectname","issueid","status","tracker","priority"])
        self._prometheus_metrics['spentime'] = GaugeMetricFamily('redmine_project_issue_spenttime_duration_hours',
                                    'Redmine Project SpentTime Duration Hours', labels=["projectname","issueid","activity"])
        self._prometheus_metrics['duedate'] = GaugeMetricFamily('redmine_project_issue_due_date',
                                    'Redmine Project Issue Done Ratio', labels=["projectname","issueid","status","tracker","priority"])
        self._prometheus_metrics['startdate'] = GaugeMetricFamily('redmine_project_issue_start_date',
                                    'Redmine Project Issue Done Ratio', labels=["projectname","issueid","status","tracker","priority"])
        self._prometheus_metrics['closeddate'] = GaugeMetricFamily('redmine_project_issue_closed_date',
                                    'Redmine Project Issue Done Ratio', labels=["projectname","issueid","status","tracker","priority"])

def parse_args():
    parser = argparse.ArgumentParser(
        description='redmine exporter args redmine address and port'
    )
    parser.add_argument(
        '-r', '--redmine',
        metavar='redmine',
        required=False,
        help='server url from the redmine api',
        default=os.environ.get('REDMINE_SERVER', 'http://redmine:80')
    )
    parser.add_argument(
        '--user',
        metavar='user',
        required=False,
        help='redmine api user',
        default=os.environ.get('REDMINE_USER')
    )
    parser.add_argument(
        '--password',
        metavar='password',
        required=False,
        help='redmine api password',
        default=os.environ.get('REDMINE_PASSWORD')
    )
    parser.add_argument(
        '-p', '--port',
        metavar='port',
        required=False,
        type=int,
        help='Listen to this port',
        default=int(os.environ.get('VIRTUAL_PORT', '9121'))
    )
    return parser.parse_args()


def main():
    try:
        args = parse_args()
        port = int(args.port)
        REGISTRY.register(RedmineCollector(args.redmine, args.user, args.password))
        start_http_server(port)
        print("Polling {}. Serving at port: {}".format(args.redmine, port))
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(" Interrupted")
        exit(0)


if __name__ == "__main__":
    main()
