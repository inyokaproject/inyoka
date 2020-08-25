#!/usr/bin/env groovy

pipeline {
  agent { label 'master' }
  options {
    buildDiscarder(logRotator(numToKeepStr: '5'))
  }
  parameters {
    booleanParam(name: 'RUN_MIGRATIONS', defaultValue: false, description: '')
    booleanParam(name: 'REBUILD_STATICS', defaultValue: true, description: '')
    booleanParam(name: 'REBUILD_VENV', defaultValue: false, description: '')
    choice(choices: 'staging\noss\ntesting', description: 'Which site should be deployed?', name: 'DEPLOY_SITE')
    text(name: 'THEME_PR_ID', defaultValue: '', description: 'Defines the PR id to use for the the theme. If empty, DEPLOY_SITE will be used as branch.')
  }
  stages {
    stage('Build and Deploy') {
      steps {
        sh """
        cd /srv/local/ubuntuusers/${params.DEPLOY_SITE}
        if ${REBUILD_VENV}
        then
          rm -rf venv
          virtualenv --python=python3 --no-download venv
          . /srv/local/ubuntuusers/${params.DEPLOY_SITE}/venv/bin/activate
          pip install --upgrade pip --no-cache-dir
          pip install -r inyoka/extra/requirements/development.txt
        else
          . /srv/local/ubuntuusers/${params.DEPLOY_SITE}/venv/bin/activate
        fi

        cd /srv/local/ubuntuusers/${params.DEPLOY_SITE}/theme
        if [ -n "${params.THEME_PR_ID}" ]
        then
            git fetch --force origin pull/${params.THEME_PR_ID}/head:pr-${params.THEME_PR_ID}
            git checkout pr-${params.THEME_PR_ID}
        else
            git checkout ${params.DEPLOY_SITE}
            git pull
        fi
        python setup.py develop

        if ${REBUILD_STATICS}
        then
            npm install
            ./node_modules/grunt-cli/bin/grunt
        else
            echo 'Not rebuildung statics'
        fi

        cd /srv/local/ubuntuusers/${params.DEPLOY_SITE}/inyoka
        git pull

        if ${RUN_MIGRATIONS}
        then
            python manage.py migrate --noinput
        else
            echo 'Not running migrations'
        fi
        
        if ${REBUILD_STATICS}
        then
            python manage.py collectstatic --noinput
        fi

        touch /srv/local/ubuntuusers/${params.DEPLOY_SITE}/restart-services
        """
      }
    }
  }
}
