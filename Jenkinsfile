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
      checkout([$class: 'GitSCM', branches: [[name: '*/staging']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'theme-ubuntuusers']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'e081c9b5-6899-40b5-a895-7c2232be3430', url: 'git@github.com:inyokaproject/theme-ubuntuusers']]])

      sh """
      requirementshash=\$(sha1sum extra/requirements/development.txt|awk '{print \$1}')

      if [ ! -d "\$HOME/venvs/\$requirementshash" ]
      then
        virtualenv --no-download ~/venvs/\$requirementshash
        . \$HOME/venvs/\$requirementshash/bin/activate
        # Workaround for pip, because it will hang forever when not updated and using the cache.
        pip install --upgrade pip --no-cache-dir
        pip install unittest-xml-reporting
        pip install -r extra/requirements/development.txt
      else
        . ~/venvs/\$requirementshash/bin/activate
      fi

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
          sh """
          requirementshash=\$(sha1sum extra/requirements/development.txt|awk '{print \$1}')
          . \$HOME/venvs/\$requirementshash/bin/activate
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
