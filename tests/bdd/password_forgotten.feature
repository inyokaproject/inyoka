@password_forgotten
Feature: Password forgotten
  A user should be able to help himself if he has forgotten his password.


  Scenario: The user has forgotten the password so he should be able to see the forgotten link
    Given I am on the "login" page
     Then I should see a link to "BASE_DOMAIN_NAME/lost_password/"

  Scenario: The user opens the lost password page
    Given I am on the "lost_password" page
     Then I should see elements
      | item     |
      | id_email |

  @skip
  Scenario: The user requests an new password to his mail
    Given I am on the "lost_password" page
     When I fill out the form
      | field    | value                |
      | id_email | test_mail@invalid.de |
     Then it should be successful
