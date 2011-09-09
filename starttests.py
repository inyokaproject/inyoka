import nose
from inyoka.testing import InyokaElasticPlugin

if __name__ == '__main__':
    nose.main(addplugins=[InyokaElasticPlugin()])
