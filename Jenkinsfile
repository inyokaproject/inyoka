#!/usr/bin/env groovy
properties([buildDiscarder(logRotator(
                                      artifactDaysToKeepStr: '',
                                      artifactNumToKeepStr: '',
                                      daysToKeepStr: '',
                                      numToKeepStr: '2')), 
                          pipelineTriggers([])
])

node {
    stage('Checkout') {
      checkout scm
      sh '''git clean -fdx'''
      sh '''rm -rf theme-ubuntuusers'''
    }

    stage('Build virtualenv') {
      sh """#!/bin/bash
      virtualenv --no-download venv
      . ./venv/bin/activate
      # Workaround for pip, because it will hang forever when not updated and using the cache.
      pip install --upgrade pip --no-cache-dir
      pip install unittest-xml-reporting
      pip install -r extra/requirements/development.txt

      git clone --depth 1 --branch staging git@github.com:inyokaproject/theme-ubuntuusers.git theme-ubuntuusers
      cd theme-ubuntuusers
      if [[ "`git branch --list ${env.BRANCH_NAME}`" ]]
      then
        echo 'Checkout out ${env.BRANCH_NAME}'
        git checkout ${env.BRANCH_NAME}
      else
        echo 'Branch not found in theme-ubuntuusers'
      fi

      python setup.py develop
      npm install
      ./node_modules/grunt-cli/bin/grunt
      cd .."""
    }

    stage('Tests') {
      def test_databases = [ "mysql", "postgresql", "sqlite" ]
      def test_runs = [:]

      for (int i = 0; i < test_databases.size(); i++) {
        def current_test_database = test_databases[i]
        test_runs["${current_test_database}"] = {
          sh """. venv/bin/activate
          python manage.py test --setting tests.settings.${current_test_database} --testrunner='xmlrunner.extra.djangotestrunner.XMLTestRunner' || true"""
        }
      }

      parallel test_runs
    }

    stage('Analyse tests') {
      step([$class: 'JUnitResultArchiver', testResults: '*.xml'])
    }

    stage('Cleanup') {
      sh '''rm -rf venv
      rm -rf theme-ubuntuusers'''
    }
}
