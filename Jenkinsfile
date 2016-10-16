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
      sh """
      virtualenv --no-download venv
      . ./venv/bin/activate
      # Workaround for pip, because it will hang forever when not updated and using the cache.
      pip install --upgrade pip --no-cache-dir
      pip install unittest-xml-reporting
      pip install -r extra/requirements/development.txt"""

      checkout([$class: 'GitSCM', branches: [[name: '*/staging']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'theme-ubuntuusers']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'e081c9b5-6899-40b5-a895-7c2232be3430', url: 'git@github.com:inyokaproject/theme-ubuntuusers']]])

      sh """. ./venv/bin/activate
      cd theme-ubuntuusers
      git checkout ${env.BRANCH_NAME} || git checkout staging

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
      step([$class: 'XUnitBuilder',
            testTimeMargin: '3000',
            thresholdMode: 1,
            thresholds: [[$class: 'FailedThreshold',
                          failureNewThreshold: '1',
                          failureThreshold: '1',
                          unstableNewThreshold: '0',
                          unstableThreshold: '0'],
                        [$class: 'SkippedThreshold',
                          failureNewThreshold: '',
                          failureThreshold: '',
                          unstableNewThreshold: '',
                          unstableThreshold: '']],
                        tools: [
                          [$class: 'JUnitType',
                            deleteOutputFiles: true,
                            failIfNotNew: true,
                            pattern: 'sqlite.xml',
                            skipNoTestFiles: false,
                            stopProcessingIfError: true],
                          [$class: 'JUnitType',
                            deleteOutputFiles: true,
                            failIfNotNew: true,
                            pattern: 'mysql.xml',
                            skipNoTestFiles: false,
                            stopProcessingIfError: true],
                          [$class: 'JUnitType',
                            deleteOutputFiles: true,
                            failIfNotNew: true,
                            pattern: 'postgresql.xml',
                            skipNoTestFiles: false,
                            stopProcessingIfError: true]]])
    }

    stage('Cleanup') {
      sh '''rm -rf venv
      rm -rf theme-ubuntuusers'''
    }
}
