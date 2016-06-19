node {
    stage 'Checkout'
    checkout scm
    sh '''git clean -fdx'''
    sh '''rm -rf theme-ubuntuusers'''

    stage 'Build virtualenv'
    sh '''virtualenv venv
    . ./venv/bin/activate
    # Workaround for pip, because it will hang forever when not updated and using the cache.
    pip install --upgrade pip --no-cache-dir
    pip install unittest-xml-reporting
    pip install -r extra/requirements/development.txt
    git clone --depth 1 --branch staging git@github.com:inyokaproject/theme-ubuntuusers.git theme-ubuntuusers
    cd theme-ubuntuusers
    python setup.py develop
    npm install
    ./node_modules/grunt-cli/bin/grunt
    cd ..'''

    stage 'Tests: mysql'
    sh '''. venv/bin/activate
    python manage.py test --setting tests.settings.mysql --testrunner="xmlrunner.extra.djangotestrunner.XMLTestRunner"'''
    step([$class: 'JUnitResultArchiver', testResults: '*.xml'])

    stage 'Tests: postgresql'
    sh '''. venv/bin/activate
    python manage.py test --setting tests.settings.postgresql --testrunner="xmlrunner.extra.djangotestrunner.XMLTestRunner"'''
    step([$class: 'JUnitResultArchiver', testResults: '*.xml'])
    
    stage 'Tests: sqlite'
    sh '''. venv/bin/activate
    python manage.py test --setting tests.settings.sqlite --testrunner="xmlrunner.extra.djangotestrunner.XMLTestRunner"'''
    step([$class: 'JUnitResultArchiver', testResults: '*.xml'])

}
