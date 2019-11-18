#!/usr/bin/env groovy

pipeline {
  agent { label 'master' }
  options {
    buildDiscarder(logRotator(numToKeepStr: '5'))
  }
  parameters {
    string(defaultValue: '', description: 'Build inyoka for specified git tag.', name: 'INYOKA_GIT_TAG')
    string(defaultValue: '', description: 'Build theme-ubuntuusers for specified git tag.', name: 'THEME_UBUNTUUSERS_GIT_TAG')
  }
  stages {
    stage('Clone Repos') {
      steps {
        deleteDir()
        checkout([$class: 'GitSCM', branches: [[name: 'refs/tags/${INYOKA_GIT_TAG}']],
                  doGenerateSubmoduleConfigurations: false,
                  extensions: [[$class: 'WipeWorkspace'], [$class: 'RelativeTargetDirectory', relativeTargetDir: 'inyoka']],
                  submoduleCfg: [],
                  userRemoteConfigs: [[credentialsId: '0a5bf4c4-bd09-43bc-908e-2030b1e968bf', url: 'git@github.com:inyokaproject/inyoka']]])

        checkout([$class: 'GitSCM', branches: [[name: 'refs/tags/${THEME_UBUNTUUSERS_GIT_TAG}']],
                  doGenerateSubmoduleConfigurations: false,
                  extensions: [[$class: 'WipeWorkspace'],
                  [$class: 'RelativeTargetDirectory', relativeTargetDir: 'theme-ubuntuusers']],
                  submoduleCfg: [],
                  userRemoteConfigs: [[credentialsId: '0a5bf4c4-bd09-43bc-908e-2030b1e968bf', url: 'git@github.com:inyokaproject/theme-ubuntuusers']]])
      }
    }
    stage('Build Virtuelenv') {
      steps {
        sh '''
        virtualenv --python=python3 --no-download venv
        . venv/bin/activate
        pip install --upgrade pip --no-cache-dir
        pip install -r inyoka/extra/requirements/production.txt
        '''
      }
    }
    stage('Build statics') {
      steps {
        dir('theme-ubuntuusers') {
          sh '''
          . ../venv/bin/activate
          python setup.py develop
          npm install
          ./node_modules/grunt-cli/bin/grunt
          '''
        }

        dir('inyoka') {
          sh '''
          . ../venv/bin/activate
          cp example_development_settings.py development_settings.py
          sed -i "s/None/'asdad'/g" development_settings.py
          sed -i "s/inyoka_theme_default/inyoka_theme_ubuntuusers/g" development_settings.py
          python manage.py collectstatic --noinput
          '''
        }
      }
    }
    stage('Pack statics') {
      steps {
        sh '''
        cd inyoka/inyoka
        package_name=inyoka-${INYOKA_GIT_TAG}_ubuntuusers-theme-${THEME_UBUNTUUSERS_GIT_TAG}_static
        mv static-collected ${package_name}
        tar -zcvf ${package_name}.tar.gz ${package_name}
        ls -la'''
        archiveArtifacts 'inyoka/inyoka/*.tar.gz'
      }
    }
  }
}
