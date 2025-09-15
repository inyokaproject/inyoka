=================
Release procedure
=================

This contains the steps required to release a new Inyoka version.
It also gives some tips for the deployment of inyoka to the target server.

Notify users
============

Before a deployment starts, notify your users.
This can be done for example via a global status message on your website or
a maintenance incident on a special status web page.

Pick a version
==============

If you want to tag a new version, take a moment to decide which version string to use.

Inyoka uses `bump-my-version <https://github.com/callowayproject/bump-my-version>`_ to partly formalize the version schema described in :doc:`releases/index`.
So, the following command shows the options you have to pick a new version:

.. code-block:: console

    bump-my-version show-bump

Theme
=====

Merge the staging branch into master. Create a new version in the theme repository.
And merge it back into staging.

.. code-block:: console

    git remote update
    git stash

    git checkout staging
    git pull --rebase

    # merge staging into master
    git checkout master
    git pull --rebase
    git merge staging --no-ff
    bump-my-version bump patch --dry-run -v # remove dry-run and verbose flags, if good
    git push
    git push -u origin v0.X.Y

    # merge master into staging back (ff for merge commit)
    git checkout staging
    git merge master
    git push

    # optionally, switch branch
    #git checkout my-cool-feature
    # optionally, restore content from stash
    #git stash pop

Inyoka
======

Basically, the same as for the theme.

.. code-block:: console

    git remote update
    git stash

    git checkout staging
    git pull --rebase

    # merge staging into master
    git checkout master
    git pull --rebase
    git merge staging --no-ff

    # add date to CHANGELOG
    vim ChangeLog.rst
    git add ChangeLog.rst
    git commit -m 'Update date of Changelog'

    bump-my-version bump patch --dry-run -v # remove dry-run and verbose flags, if good


    git push
    git push -u origin v0.X.Y

    # merge master into staging back (ff for merge commit)
    git checkout staging
    git merge master
    git push

    # optionally, switch branch
    #git checkout my-cool-feature
    # optionally, restore content from stash
    #git stash pop

docker-setup
============

Merge `main` (with newest changes) into the branch `uu-production`

.. code-block:: console

    git checkout uu-production
    git merge main
    git push


Build docker images
===================

Start the `action
<https://github.com/inyokaproject/docker-setup/actions/workflows/build-ubuntuusers-docker-images.yml>`_
on the Inyoka branches

 * (optional) staging
 * master



Deploy to target
================

Start VPN, if needed.

Connect to target where Inyoka is running via SSH

.. code-block:: console

    eval $(ssh-agent)
    ssh-add ~/.ssh/ubuntuusers_ed25519
    ssh uu-brain

Use ansible to deploy Inyoka

.. code-block:: console

    cd ~/Dev/uu-ansible
    source activate.sh
    ansible-playbook site.yml --check --diff -t inyoka -l brain.ubuntu-eu.org

(Remove ``--check``, if everything looks good, to make changes)
