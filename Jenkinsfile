#!/usr/bin/env groovy

def runTestOnDatabase(String database) {
  sh """
  . ~/venvs/${requirementshash}/bin/activate
  coverage run --branch manage.py test --setting tests.settings.${database} --testrunner='xmlrunner.extra.djangotestrunner.XMLTestRunner' || true
  coverage xml"""
}

pipeline{
  agent { label 'inyoka-slave' }
  options {
    buildDiscarder(logRotator(numToKeepStr: '10'))
  }
  stages {
    stage('Prepare build') {
      parallel{
        stage('Build Virtualenv') {
          steps {
            script {
              requirementshash = sh returnStdout: true,
                                    script: "cat extra/requirements/development.txt extra/requirements/production.txt | sha256sum | awk '{print \$1}'"
              requirementshash = requirementshash.trim()
            }

            sh """
            if [ ! -d '~/venvs/${requirementshash}' ]
            then
              virtualenv ~/venvs/${requirementshash}
              . ~/venvs/${requirementshash}/bin/activate
              pip install unittest-xml-reporting
              pip install -r extra/requirements/development.txt
            fi"""
          }
        }
        stage('Theme checkout') {
          steps{
            dir('theme-ubuntuusers') {
              git branch: 'staging', url: 'git@github.com:inyokaproject/theme-ubuntuusers'

              sh """
              git checkout ${env.BRANCH_NAME} || git checkout staging

              npm install
              ./node_modules/grunt-cli/bin/grunt """
            }
          }
        }
      }
    }
    stage('Link theme') {
      steps {
        dir('theme-ubuntuusers') {
          sh """
            . ~/venvs/${requirementshash}/bin/activate
            python setup.py develop """
        }
      }
    }
    stage('Tests') {
      parallel{
        stage('Mysql') {
          steps{
            runTestOnDatabase('mysql')
          }
        }
        stage('PostgreSQL') {
          steps{
            runTestOnDatabase('postgresql')
          }
        }
        stage('SQLite') {
          steps{
            runTestOnDatabase('sqlite')
          }
        }
      }
    }
    stage('Analyse tests') {
      steps {
        junit 'sqlite.xml,mysql.xml,postgresql.xml'
        step([$class: 'CoberturaPublisher',
              autoUpdateHealth: false,
              autoUpdateStability: false,
              coberturaReportFile: 'coverage.xml',
              failUnhealthy: false,
              failUnstable: false,
              maxNumberOfBuilds: 0,
              onlyStable: false,
              sourceEncoding: 'ASCII',
              zoomCoverageChart: false])
      }
    }
  }
}