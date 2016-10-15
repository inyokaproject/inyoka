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

    stage('Tests: mysql') {
      sh '''. venv/bin/activate
      python manage.py test --setting tests.settings.mysql --testrunner="xmlrunner.extra.djangotestrunner.XMLTestRunner" || true'''
    }

    stage('Tests: postgresql') {
      sh '''. venv/bin/activate
      python manage.py test --setting tests.settings.postgresql --testrunner="xmlrunner.extra.djangotestrunner.XMLTestRunner" || true'''
    }

    stage('Tests: sqlite') {
      sh '''. venv/bin/activate
      python manage.py test --setting tests.settings.sqlite --testrunner="xmlrunner.extra.djangotestrunner.XMLTestRunner" || true'''
    }

    stage('Analyse tests') {
      step([$class: 'JUnitResultArchiver', testResults: '*.xml'])
    }

    stage('Cleanup') {
      sh '''rm -rf venv
      rm -rf theme-ubuntuusers'''
    }
}
